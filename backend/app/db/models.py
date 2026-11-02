"""Core database models for Identity, Tenancy, and Hash-Chained Audit Trails."""

from datetime import datetime
from enum import Enum
import uuid
from typing import Optional, Any
from sqlalchemy import (
    String, Text, Boolean, ForeignKey, Integer, Index, CheckConstraint,
    DateTime, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, utc_now


class UserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    INSTITUTION_ADMIN = "institution_admin"
    OPERATOR = "operator"
    VERIFIER = "verifier"
    HOLDER = "holder"


class InstitutionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"


class KeyStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"
    COMPROMISED = "compromised"


class Institution(Base):
    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # university, college, board, polytechnic
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    registration_no: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    official_domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[InstitutionStatus] = mapped_column(
        String(32), default=InstitutionStatus.PENDING, nullable=False
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    keys: Mapped[list["InstitutionKey"]] = relationship(back_populates="institution", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="institution")
    documents: Mapped[list["InstitutionDocument"]] = relationship(back_populates="institution", cascade="all, delete-orphan")


class InstitutionDocument(Base):
    __tablename__ = "institution_documents"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)  # registration_cert, aicte_approval, ugc_letter
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    institution: Mapped["Institution"] = relationship(back_populates="documents")


class InstitutionKey(Base):
    __tablename__ = "institution_keys"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    key_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)  # First 8 bytes of SHA-256 in hex
    public_key: Mapped[str] = mapped_column(String(128), nullable=False)  # Base64 or Hex Ed25519 public key
    status: Mapped[KeyStatus] = mapped_column(String(32), default=KeyStatus.ACTIVE, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    compromised_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    domain_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    domain_check_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    institution: Mapped["Institution"] = relationship(back_populates="keys")


class ServerHeldKey(Base):
    """Encrypted private keys for ServerSigner. Separated from public keys."""
    __tablename__ = "server_held_keys"

    key_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    encrypted_private_key: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    iv: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    tag: Mapped[bytes] = mapped_column(BYTEA, nullable=False)


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(32), nullable=False)
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    totp_secret_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped[Optional["Institution"]] = relationship(back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class AuditLog(Base):
    """Immutable, append-only, and hash-chained audit log table."""
    __tablename__ = "audit_log"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # institution_applied, approved, key_rotated, etc.
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)  # institution, user, certificate
    object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # Salted SHA-256 of IP address
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    row_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    __table_args__ = (
        Index("idx_audit_log_object", "object_type", "object_id"),
        Index("idx_audit_log_action", "action"),
    )
