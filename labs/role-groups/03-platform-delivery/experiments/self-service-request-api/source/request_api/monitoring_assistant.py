"""Bounded advisory analysis for sanitized monitoring signals.

The deterministic monitoring pipeline remains authoritative.  This module never
accepts raw logs, labels, identities, network addresses, or an open-ended prompt.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,80}$")


class MonitoringSignal(BaseModel):
    """A metric-only anomaly result safe for bounded advisory processing."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,64}$")
    observed_at: datetime
    source: Literal["PROMETHEUS", "OPENTELEMETRY", "SYNTHETIC_TEST"]
    metric_name: str = Field(pattern=r"^[A-Za-z_:][A-Za-z0-9_:]{0,127}$")
    current_value: float = Field(allow_inf_nan=False)
    baseline_value: float = Field(allow_inf_nan=False)
    anomaly_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    state: Literal["NORMAL", "WARNING", "REVIEW_REQUIRED", "ANOMALY_DETECTED"]


class MonitoringAssistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_goal: Literal["TRIAGE_SUMMARY", "TREND_EXPLANATION", "OPERATOR_CHECKLIST"]
    signals: list[MonitoringSignal] = Field(min_length=1, max_length=20)


@dataclass(frozen=True, slots=True)
class MonitoringAdvisory:
    text: str
    source: str
    model: str
    input_units: int
    output_units: int
    provider_connected: bool


class MonitoringAssistantError(RuntimeError):
    pass


def _bounded_payload(payload: MonitoringAssistRequest) -> dict:
    return {
        "analysis_goal": payload.analysis_goal,
        "signals": [
            {
                "signal_id": signal.signal_id,
                "observed_at": signal.observed_at.isoformat(),
                "source": signal.source,
                "metric_name": signal.metric_name,
                "current_value": signal.current_value,
                "baseline_value": signal.baseline_value,
                "anomaly_score": signal.anomaly_score,
                "state": signal.state,
            }
            for signal in payload.signals
        ],
    }


def local_advisory(payload: MonitoringAssistRequest) -> MonitoringAdvisory:
    """Produce a deterministic development advisory without a model call."""

    ordered = sorted(payload.signals, key=lambda item: item.anomaly_score, reverse=True)
    top = ordered[0]
    flagged = sum(item.state != "NORMAL" for item in ordered)
    text = (
        f"{len(ordered)}개 정제 지표 중 {flagged}개가 검토 상태입니다. "
        f"우선 확인 대상은 {top.metric_name}이며 anomaly score는 {top.anomaly_score:.2f}입니다. "
        "기존 대시보드와 런북에서 원인을 확인하고, 모든 차단·복구 조치는 운영자 승인을 거치세요."
    )
    serialized = json.dumps(_bounded_payload(payload), ensure_ascii=False, sort_keys=True)
    return MonitoringAdvisory(
        text=text,
        source="LOCAL_DETERMINISTIC_ASSISTANT",
        model="monitoring-local-advisory",
        input_units=len(serialized),
        output_units=len(text),
        provider_connected=False,
    )


def _read_bearer_token(token_file: str) -> str:
    path = Path(token_file)
    if not path.is_absolute():
        raise MonitoringAssistantError("monitoring assistant token file must be an absolute external path")
    try:
        credential_value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise MonitoringAssistantError("monitoring assistant credential is unavailable") from exc
    if not credential_value or len(credential_value) > 8192 or any(char.isspace() for char in credential_value):
        raise MonitoringAssistantError("monitoring assistant credential is invalid")
    return credential_value


def _response_text(result: dict) -> str:
    direct = result.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts: list[str] = []
    for item in result.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                parts.append(content["text"].strip())
    return "\n".join(part for part in parts if part).strip()


def openai_advisory(
    payload: MonitoringAssistRequest,
    *,
    model: str,
    token_file: str,
    timeout_seconds: float,
    transport: httpx.BaseTransport | None = None,
) -> MonitoringAdvisory:
    """Call the OpenAI Responses API with a server-side service credential."""

    if not MODEL_PATTERN.fullmatch(model):
        raise MonitoringAssistantError("monitoring assistant model is not configured")
    credential_value = _read_bearer_token(token_file)
    bounded = _bounded_payload(payload)
    body = {
        "model": model,
        "store": False,
        "max_output_tokens": 500,
        "instructions": (
            "You are a monitoring advisory assistant. Analyze only the supplied sanitized numeric signals. "
            "Do not infer people, tenants, hosts, IP addresses, secrets, raw logs, or financial activity. "
            "Do not claim authority to block, remediate, approve, or change infrastructure. "
            "Return a concise Korean explanation, uncertainty, and a human operator checklist."
        ),
        "input": json.dumps(bounded, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    }
    try:
        with httpx.Client(transport=transport, timeout=timeout_seconds) as client:
            response = client.post(
                OPENAI_RESPONSES_URL,
                headers={"Authorization": f"Bearer {credential_value}", "Content-Type": "application/json"},
                json=body,
            )
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError, OSError) as exc:
        raise MonitoringAssistantError("monitoring assistant provider is unavailable") from exc
    text = _response_text(result)
    if not text or len(text) > 4000:
        raise MonitoringAssistantError("monitoring assistant returned an invalid response")
    usage = result.get("usage") or {}
    return MonitoringAdvisory(
        text=text,
        source="OPENAI_RESPONSES_API",
        model=model,
        input_units=int(usage.get("input_tokens") or 0),
        output_units=int(usage.get("output_tokens") or 0),
        provider_connected=True,
    )
