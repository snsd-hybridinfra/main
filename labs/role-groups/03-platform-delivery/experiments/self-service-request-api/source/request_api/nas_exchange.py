"""Metadata-only local simulator for the bounded NAS exchange workflow.

This module never opens, copies, mounts, or scans a file. It accepts only the
sanitized verdicts that a future approved scanner adapter may produce. Runtime
NAS and scanner integration therefore remains NOT_VALIDATED.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Any


ALLOWED_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}
POLICY_MAX_BYTES = 100 * 1024 * 1024
ABSOLUTE_MAX_BYTES = 1024 * 1024 * 1024
MAX_ARCHIVE_DEPTH = 3
OPAQUE_ACTOR = re.compile(r"actor_[0-9a-f]{16}")
EXCHANGE_ID = re.compile(r"NASX-[A-Z0-9][A-Z0-9-]{5,47}")
DIGEST = re.compile(r"[0-9a-f]{64}")


class NasExchangeError(ValueError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Intake:
    exchange_id: str
    object_digest: str
    size_bytes: int
    declared_extension: str
    declared_media_type: str
    submitter_ref: str
    synthetic_data_attested: bool
    observed_at: str


@dataclass(frozen=True)
class ScanVerdict:
    detected_extension: str
    detected_media_type: str
    digest_verified: bool
    malware_detected: bool
    content_policy_passed: bool
    archive_depth: int
    scan_latency_seconds: float
    observed_at: str


def _timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NasExchangeError("observed_at must be an ISO-8601 timestamp", "INVALID_INPUT") from exc
    if parsed.tzinfo is None:
        raise NasExchangeError("observed_at must include a timezone", "INVALID_INPUT")
    return parsed.isoformat()


def _actor(value: str) -> str:
    if not OPAQUE_ACTOR.fullmatch(value):
        raise NasExchangeError("actor reference must be opaque", "INVALID_ACTOR")
    return value


class NasExchangeEngine:
    """In-memory deterministic workflow used only for local contract tests."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._sequence = 0
        self._auth_failures = 0
        self._scan_latencies: list[float] = []
        self._lock = RLock()

    def _transition(
        self,
        item: dict[str, Any],
        target: str,
        *,
        event: str,
        observed_at: str,
        reason_code: str | None = None,
    ) -> None:
        timestamp = _timestamp(observed_at)
        self._sequence += 1
        previous = item.get("state")
        item["state"] = target
        item["reason_code"] = reason_code
        item["audit"].append(
            {
                "sequence": self._sequence,
                "event": event,
                "from_state": previous,
                "to_state": target,
                "observed_at": timestamp,
                "reason_code": reason_code,
            }
        )

    def receive(self, intake: Intake) -> dict[str, Any]:
        with self._lock:
            _timestamp(intake.observed_at)
            if not EXCHANGE_ID.fullmatch(intake.exchange_id):
                raise NasExchangeError("exchange_id is invalid", "INVALID_INPUT")
            if intake.exchange_id in self._items:
                raise NasExchangeError("exchange_id already exists", "DUPLICATE_EXCHANGE")
            if not DIGEST.fullmatch(intake.object_digest):
                raise NasExchangeError("object digest must be lowercase SHA-256", "INVALID_INPUT")
            if type(intake.size_bytes) is not int or not 0 < intake.size_bytes <= ABSOLUTE_MAX_BYTES:
                raise NasExchangeError("size is outside the absolute intake boundary", "INVALID_INPUT")
            expected_media = ALLOWED_TYPES.get(intake.declared_extension)
            if expected_media is None or expected_media != intake.declared_media_type:
                raise NasExchangeError("declared file type is outside policy", "FILE_TYPE_DENIED")
            item = {
                "exchange_id": intake.exchange_id,
                "object_digest": intake.object_digest,
                "size_bytes": intake.size_bytes,
                "declared_extension": intake.declared_extension,
                "declared_media_type": intake.declared_media_type,
                "submitter_ref": _actor(intake.submitter_ref),
                "synthetic_data_attested": intake.synthetic_data_attested,
                "state": None,
                "reason_code": None,
                "audit": [],
            }
            self._items[intake.exchange_id] = item
            self._transition(
                item,
                "RECEIVED",
                event="INTAKE_RECORDED",
                observed_at=intake.observed_at,
            )
            return self.view(intake.exchange_id)

    def quarantine(self, exchange_id: str, *, observed_at: str) -> dict[str, Any]:
        with self._lock:
            item = self._require(exchange_id, "RECEIVED")
            self._transition(
                item,
                "QUARANTINED",
                event="IMMUTABLE_QUARANTINE_RECORDED",
                observed_at=observed_at,
            )
            return self.view(exchange_id)

    def scan(self, exchange_id: str, verdict: ScanVerdict) -> dict[str, Any]:
        with self._lock:
            item = self._require(exchange_id, "QUARANTINED")
            if not 0 <= verdict.archive_depth <= 100:
                raise NasExchangeError("archive depth is invalid", "INVALID_INPUT")
            if not 0 <= verdict.scan_latency_seconds <= 3600:
                raise NasExchangeError("scan latency is invalid", "INVALID_INPUT")
            _timestamp(verdict.observed_at)
            self._transition(
                item,
                "SCANNING",
                event="SANITIZED_SCAN_STARTED",
                observed_at=verdict.observed_at,
            )
            self._scan_latencies.append(float(verdict.scan_latency_seconds))
            reason = self._scan_reason(item, verdict)
            target = "REJECTED" if reason else "PENDING_APPROVAL"
            self._transition(
                item,
                target,
                event="SCAN_REJECTED" if reason else "SCAN_PASSED",
                observed_at=verdict.observed_at,
                reason_code=reason,
            )
            return self.view(exchange_id)

    @staticmethod
    def _scan_reason(item: dict[str, Any], verdict: ScanVerdict) -> str | None:
        if not item["synthetic_data_attested"]:
            return "SYNTHETIC_ATTESTATION_REQUIRED"
        if item["size_bytes"] > POLICY_MAX_BYTES:
            return "SIZE_LIMIT_EXCEEDED"
        if verdict.malware_detected:
            return "MALWARE_DETECTED"
        if not verdict.digest_verified:
            return "DIGEST_MISMATCH"
        if verdict.archive_depth > MAX_ARCHIVE_DEPTH:
            return "ARCHIVE_LIMIT_EXCEEDED"
        if not verdict.content_policy_passed:
            return "CONTENT_POLICY_DENIED"
        if (
            ALLOWED_TYPES.get(verdict.detected_extension) != verdict.detected_media_type
            or verdict.detected_extension != item["declared_extension"]
            or verdict.detected_media_type != item["declared_media_type"]
        ):
            return "FILE_TYPE_MISMATCH"
        return None

    def decide(
        self,
        exchange_id: str,
        *,
        reviewer_ref: str,
        mfa_verified: bool,
        approved: bool,
        object_digest: str,
        observed_at: str,
    ) -> dict[str, Any]:
        with self._lock:
            item = self._require(exchange_id, "PENDING_APPROVAL")
            try:
                reviewer = _actor(reviewer_ref)
                if not mfa_verified:
                    raise NasExchangeError("reviewer MFA is required", "MFA_REQUIRED")
                if reviewer == item["submitter_ref"]:
                    raise NasExchangeError("self approval is denied", "SELF_APPROVAL_DENIED")
                if object_digest != item["object_digest"]:
                    raise NasExchangeError("approval digest mismatch", "DIGEST_MISMATCH")
            except NasExchangeError:
                self._auth_failures += 1
                raise
            self._transition(
                item,
                "RELEASED" if approved else "REJECTED",
                event="DIGEST_APPROVED" if approved else "REVIEW_REJECTED",
                observed_at=observed_at,
                reason_code=None if approved else "HUMAN_REJECTED",
            )
            return self.view(exchange_id)

    def expire(self, exchange_id: str, *, observed_at: str) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(exchange_id)
            if item is None or item["state"] not in {"RELEASED", "REJECTED"}:
                raise NasExchangeError("exchange is not expirable", "INVALID_TRANSITION")
            self._transition(
                item,
                "EXPIRED",
                event="RETENTION_EXPIRED",
                observed_at=observed_at,
            )
            return self.view(exchange_id)

    def _require(self, exchange_id: str, expected_state: str) -> dict[str, Any]:
        item = self._items.get(exchange_id)
        if item is None:
            raise NasExchangeError("exchange does not exist", "NOT_FOUND")
        if item["state"] != expected_state:
            raise NasExchangeError("exchange transition is invalid", "INVALID_TRANSITION")
        return item

    def view(self, exchange_id: str) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(exchange_id)
            if item is None:
                raise NasExchangeError("exchange does not exist", "NOT_FOUND")
            return deepcopy(
                {
                    key: value
                    for key, value in item.items()
                    if key not in {"submitter_ref", "synthetic_data_attested"}
                }
            )

    def metrics(self) -> dict[str, int | float]:
        with self._lock:
            audit = [event for item in self._items.values() for event in item["audit"]]
            latencies = list(self._scan_latencies)
            return {
                "FILES_RECEIVED": sum(event["to_state"] == "RECEIVED" for event in audit),
                "FILES_RELEASED": sum(event["to_state"] == "RELEASED" for event in audit),
                "FILES_REJECTED": sum(event["to_state"] == "REJECTED" for event in audit),
                "SCAN_LATENCY_SECONDS": round(sum(latencies) / len(latencies), 6) if latencies else 0.0,
                "QUEUE_DEPTH": sum(
                    item["state"] in {"RECEIVED", "QUARANTINED", "SCANNING", "PENDING_APPROVAL"}
                    for item in self._items.values()
                ),
                "CAPACITY_PERCENT": 0.0,
                "AUTH_FAILURES": self._auth_failures,
            }
