"""Authentication and authorization schemas."""

from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field
from backend.app.db.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    totp_code: Optional[str] = Field(default=None, min_length=6, max_length=6)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 900  # 15 minutes
    role: UserRole
    institution_id: Optional[uuid.UUID] = None
    requires_totp_setup: bool = False


class TOTPEnrollResponse(BaseModel):
    totp_secret: str
    provisioning_uri: str


class TOTPVerifyRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    institution_id: Optional[uuid.UUID]
    totp_enabled: bool
