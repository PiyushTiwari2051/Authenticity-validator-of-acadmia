"""Institution schemas for application, approval, and public metadata."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field
from backend.app.db.models import InstitutionStatus, KeyStatus


class InstitutionApplyRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    type: str = Field(min_length=2, max_length=64, description="university, college, board, polytechnic")
    state: str = Field(min_length=2, max_length=64)
    registration_no: str = Field(min_length=3, max_length=128)
    official_domain: str = Field(min_length=3, max_length=255)


class InstitutionResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    state: str
    registration_no: str
    official_domain: str
    status: InstitutionStatus
    approved_at: Optional[datetime]
    created_at: datetime


class InstitutionPublicResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    state: str
    official_domain: str
    status: InstitutionStatus
    approved_at: Optional[datetime]
    active_key_ids: list[str]


class KeyRegistrationRequest(BaseModel):
    public_key: str = Field(description="Base64 or Hex Ed25519 public key")


class KeyResponse(BaseModel):
    key_id: str
    public_key: str
    status: KeyStatus
    valid_from: datetime
    retired_at: Optional[datetime]
    domain_check_ok: bool
