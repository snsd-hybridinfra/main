from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GrantCreate(BaseModel):
    request_id: str
    idempotency_key: str = Field(min_length=1, max_length=128)
    subject_id: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(min_length=1)
    duration_hours: int = Field(ge=1, le=24 * 90)
    event_version: int = Field(ge=3)
    retry_count: int = Field(default=0, ge=0)


class GrantView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grant_id: str
    request_id: str
    idempotency_key: str
    subject_id: str
    scopes: list[str]
    status: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    event_version: int
    retry_count: int
    callback_status: str
    last_error: str | None
    updated_at: datetime


class GrantIssued(BaseModel):
    grant: GrantView
    token: str
    callback_status: str


class GrantActionResult(BaseModel):
    grant: GrantView
    callback_status: str
    deprovision_status: str = "NOT_REQUESTED"


class BoundGrantRevoke(BaseModel):
    request_id: str = Field(min_length=1, max_length=36)
    owner_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=5, max_length=500)


class GrantValidation(BaseModel):
    active: bool
    grant_id: str
    request_id: str
    subject_id: str
    scopes: list[str]
    expires_at: datetime


class ProtectedResource(BaseModel):
    message: str
    grant_id: str
    subject_id: str


class HealthView(BaseModel):
    status: str


class DemoResetResult(BaseModel):
    status: Literal["reset"] = "reset"
    deleted: dict[str, int]
