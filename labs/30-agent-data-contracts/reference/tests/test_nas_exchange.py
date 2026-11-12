from __future__ import annotations

import pytest

from request_api.nas_exchange import Intake, NasExchangeEngine, NasExchangeError, ScanVerdict


DIGEST = "a" * 64
SUBMITTER = "actor_1111111111111111"
REVIEWER = "actor_2222222222222222"


def intake(**changes) -> Intake:
    values = {
        "exchange_id": "NASX-TEST-0001",
        "object_digest": DIGEST,
        "size_bytes": 4096,
        "declared_extension": ".csv",
        "declared_media_type": "text/csv",
        "submitter_ref": SUBMITTER,
        "synthetic_data_attested": True,
        "observed_at": "2026-10-02T15:00:00+09:00",
    }
    values.update(changes)
    return Intake(**values)


def verdict(**changes) -> ScanVerdict:
    values = {
        "detected_extension": ".csv",
        "detected_media_type": "text/csv",
        "digest_verified": True,
        "malware_detected": False,
        "content_policy_passed": True,
        "archive_depth": 0,
        "scan_latency_seconds": 1.25,
        "observed_at": "2026-10-02T15:01:00+09:00",
    }
    values.update(changes)
    return ScanVerdict(**values)


def test_approved_digest_bound_exchange_and_numeric_metrics() -> None:
    engine = NasExchangeEngine()
    assert engine.receive(intake())["state"] == "RECEIVED"
    assert engine.quarantine("NASX-TEST-0001", observed_at="2026-10-02T15:00:30+09:00")["state"] == "QUARANTINED"
    assert engine.scan("NASX-TEST-0001", verdict())["state"] == "PENDING_APPROVAL"
    released = engine.decide(
        "NASX-TEST-0001",
        reviewer_ref=REVIEWER,
        mfa_verified=True,
        approved=True,
        object_digest=DIGEST,
        observed_at="2026-10-02T15:02:00+09:00",
    )
    assert released["state"] == "RELEASED"
    assert engine.expire("NASX-TEST-0001", observed_at="2026-10-03T15:02:00+09:00")["state"] == "EXPIRED"
    assert set(engine.metrics()) == {
        "FILES_RECEIVED", "FILES_RELEASED", "FILES_REJECTED", "SCAN_LATENCY_SECONDS",
        "QUEUE_DEPTH", "CAPACITY_PERCENT", "AUTH_FAILURES",
    }
    assert engine.metrics()["FILES_RELEASED"] == 1
    assert "submitter_ref" not in released


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"malware_detected": True}, "MALWARE_DETECTED"),
        ({"digest_verified": False}, "DIGEST_MISMATCH"),
        ({"archive_depth": 4}, "ARCHIVE_LIMIT_EXCEEDED"),
        ({"content_policy_passed": False}, "CONTENT_POLICY_DENIED"),
        ({"detected_extension": ".txt", "detected_media_type": "text/plain"}, "FILE_TYPE_MISMATCH"),
    ],
)
def test_scanner_policy_rejections_are_deterministic(changes, reason) -> None:
    engine = NasExchangeEngine()
    engine.receive(intake())
    engine.quarantine("NASX-TEST-0001", observed_at="2026-10-02T15:00:30+09:00")
    rejected = engine.scan("NASX-TEST-0001", verdict(**changes))
    assert rejected["state"] == "REJECTED"
    assert rejected["reason_code"] == reason
    assert engine.metrics()["FILES_REJECTED"] == 1


@pytest.mark.parametrize(
    ("intake_changes", "reason"),
    [
        ({"synthetic_data_attested": False}, "SYNTHETIC_ATTESTATION_REQUIRED"),
        ({"size_bytes": 100 * 1024 * 1024 + 1}, "SIZE_LIMIT_EXCEEDED"),
    ],
)
def test_intake_policy_boundaries_reject_before_approval(intake_changes, reason) -> None:
    engine = NasExchangeEngine()
    engine.receive(intake(**intake_changes))
    engine.quarantine("NASX-TEST-0001", observed_at="2026-10-02T15:00:30+09:00")
    rejected = engine.scan("NASX-TEST-0001", verdict())
    assert rejected["state"] == "REJECTED"
    assert rejected["reason_code"] == reason


def test_invalid_scan_metadata_does_not_advance_state() -> None:
    engine = NasExchangeEngine()
    engine.receive(intake())
    engine.quarantine("NASX-TEST-0001", observed_at="2026-10-02T15:00:30+09:00")
    with pytest.raises(NasExchangeError) as caught:
        engine.scan("NASX-TEST-0001", verdict(scan_latency_seconds=-1))
    assert caught.value.code == "INVALID_INPUT"
    assert engine.view("NASX-TEST-0001")["state"] == "QUARANTINED"


def test_invalid_intake_timestamp_does_not_reserve_exchange_id() -> None:
    engine = NasExchangeEngine()
    with pytest.raises(NasExchangeError) as caught:
        engine.receive(intake(observed_at="not-a-timestamp"))
    assert caught.value.code == "INVALID_INPUT"
    assert engine.metrics()["FILES_RECEIVED"] == 0
    assert engine.receive(intake())["state"] == "RECEIVED"


def test_active_or_unapproved_declared_type_is_denied_without_record() -> None:
    engine = NasExchangeEngine()
    with pytest.raises(NasExchangeError) as caught:
        engine.receive(intake(declared_extension=".exe", declared_media_type="application/octet-stream"))
    assert caught.value.code == "FILE_TYPE_DENIED"
    assert engine.metrics()["FILES_RECEIVED"] == 0


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"reviewer_ref": SUBMITTER, "mfa_verified": True, "object_digest": DIGEST}, "SELF_APPROVAL_DENIED"),
        ({"reviewer_ref": REVIEWER, "mfa_verified": False, "object_digest": DIGEST}, "MFA_REQUIRED"),
        ({"reviewer_ref": REVIEWER, "mfa_verified": True, "object_digest": "b" * 64}, "DIGEST_MISMATCH"),
    ],
)
def test_review_authorization_fails_closed(kwargs, code) -> None:
    engine = NasExchangeEngine()
    engine.receive(intake())
    engine.quarantine("NASX-TEST-0001", observed_at="2026-10-02T15:00:30+09:00")
    engine.scan("NASX-TEST-0001", verdict())
    with pytest.raises(NasExchangeError) as caught:
        engine.decide(
            "NASX-TEST-0001",
            approved=True,
            observed_at="2026-10-02T15:02:00+09:00",
            **kwargs,
        )
    assert caught.value.code == code
    assert engine.metrics()["AUTH_FAILURES"] == 1
    assert engine.view("NASX-TEST-0001")["state"] == "PENDING_APPROVAL"


def test_contract_never_accepts_filename_content_or_raw_scanner_output() -> None:
    assert set(Intake.__dataclass_fields__) == {
        "exchange_id", "object_digest", "size_bytes", "declared_extension",
        "declared_media_type", "submitter_ref", "synthetic_data_attested", "observed_at",
    }
    assert set(ScanVerdict.__dataclass_fields__) == {
        "detected_extension", "detected_media_type", "digest_verified", "malware_detected",
        "content_policy_passed", "archive_depth", "scan_latency_seconds", "observed_at",
    }
