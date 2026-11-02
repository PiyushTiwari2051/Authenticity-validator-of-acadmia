"""Phase 2 & Phase 3 Core Models:
- Certificate model with RFC 8785 canonical bytes, Ed25519 signature, payload JSONB.
- Revocation model with signed statements.
- Batches & Batch Entries for Merkle tree transparency.
- Verifications & Findings for explainable multi-signal audit.
- Share Grants for holder-governed selective disclosure.
"""

from datetime import datetime
from enum import Enum
import uuid
from typing import Optional, Any
from sqlalchemy import (
    String, Text, Boolean, ForeignKey, Integer, Index,
    DateTime, Float, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, utc_now
from backend.app.db.models import Institution, InstitutionKey, User


class CertificateStatus(str, Enum):
    ISSUED = "issued"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class BatchAnchorKind(str, Enum):
    LOG = "log"
    EVM_TESTNET = "evm-testnet"


class LeafType(str, Enum):
    CERT = "cert"
    REVOCATION = "revocation"
    KEY_EVENT = "key_event"


class Certificate(Base):
    """Core academic certificate signed envelope entity."""
    __tablename__ = "certificates"

    certificate_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False
    )
    key_id: Mapped[str] = mapped_column(String(16), nullable=False)
    canonical_payload: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)  # Hex-encoded 64-byte Ed25519 signature
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    holder_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    enrolment_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # Salted SHA-256
    status: Mapped[CertificateStatus] = mapped_column(String(32), default=CertificateStatus.ISSUED, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    supersedes_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pdf_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    institution: Mapped["Institution"] = relationship()
    revocation: Mapped[Optional["Revocation"]] = relationship(back_populates="certificate", uselist=False)


class Revocation(Base):
    """Signed revocation statement for invalidated certificates."""
    __tablename__ = "revocations"

    certificate_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("certificates.certificate_id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)  # ISSUED_IN_ERROR, DEGREE_WITHDRAWN, etc.
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    operator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    signed_statement: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)

    certificate: Mapped["Certificate"] = relationship(back_populates="revocation")


class Batch(Base):
    """Merkle tree transparency batch anchoring certificates and revocations."""
    __tablename__ = "batches"

    batch_id: Mapped[int] = mapped_column(Integer, unique=True, autoincrement=True, nullable=False)
    root: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA-256 Merkle root
    previous_root: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # Chained root
    entry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    platform_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    anchor_kind: Mapped[str] = mapped_column(String(32), default=BatchAnchorKind.LOG.value, nullable=False)
    anchor_receipt: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    anchored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    entries: Mapped[list["BatchEntry"]] = relationship(back_populates="batch", cascade="all, delete-orphan")


class BatchEntry(Base):
    """Individual leaf in a Merkle batch."""
    __tablename__ = "batch_entries"

    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)
    leaf_index: Mapped[int] = mapped_column(Integer, nullable=False)
    leaf_type: Mapped[str] = mapped_column(String(32), nullable=False)  # cert, revocation, key_event
    ref_id: Mapped[str] = mapped_column(String(128), nullable=False)
    leaf_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    batch: Mapped["Batch"] = relationship(back_populates="entries")

    __table_args__ = (
        Index("idx_batch_leaf", "batch_id", "leaf_index", unique=True),
    )


class Verification(Base):
    """Audit record of a public or registered verification query."""
    __tablename__ = "verifications"

    method: Mapped[str] = mapped_column(String(32), nullable=False)  # qr, id, upload
    certificate_id: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    verdict: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    verifier_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    client_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)  # Salted client hash
    file_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    findings: Mapped[list["VerificationFinding"]] = relationship(back_populates="verification", cascade="all, delete-orphan")


class VerificationFinding(Base):
    """Fine-grained explainable finding for each internal check performed."""
    __tablename__ = "verification_findings"

    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verifications.id", ondelete="CASCADE"), nullable=False
    )
    check_name: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # pass, fail, warn, skipped
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    verification: Mapped["Verification"] = relationship(back_populates="findings")


class ShareGrant(Base):
    """Selective disclosure token controlling what public verifiers see."""
    __tablename__ = "share_grants"

    certificate_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("certificates.certificate_id", ondelete="CASCADE"), nullable=False
    )
    holder_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    fields_allowed: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
