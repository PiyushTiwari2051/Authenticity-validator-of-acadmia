"""Append-only, hash-chained audit logging service.
Guarantees tamper-evidence: modifying any row invalidates the entire hash chain.
"""

import hashlib
import json
from typing import Any, Optional
import uuid
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models import AuditLog
from backend.app.core.logging import logger

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def compute_audit_hash(
    prev_hash: str,
    actor_id: Optional[str],
    actor_role: str,
    action: str,
    object_type: str,
    object_id: str,
    ip_hash: str,
    detail_json: dict[str, Any],
) -> str:
    """Deterministically compute SHA-256 hash chaining previous audit entry."""
    # Deterministic canonical string
    canonical_detail = json.dumps(detail_json, sort_keys=True, separators=(",", ":"))
    payload = (
        f"{prev_hash}|"
        f"{actor_id or ''}|"
        f"{actor_role}|"
        f"{action}|"
        f"{object_type}|"
        f"{object_id}|"
        f"{ip_hash}|"
        f"{canonical_detail}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def write_audit_entry(
    db: AsyncSession,
    actor_id: Optional[uuid.UUID],
    actor_role: str,
    action: str,
    object_type: str,
    object_id: str,
    ip_hash: str,
    detail_json: dict[str, Any],
) -> AuditLog:
    """Append a new verified hash-chained audit record."""
    # Fetch latest audit row to get prev_hash
    stmt = select(AuditLog.row_hash).order_by(desc(AuditLog.created_at)).limit(1)
    result = await db.execute(stmt)
    latest_hash = result.scalar_one_or_none()

    prev_hash = latest_hash if latest_hash is not None else GENESIS_HASH
    actor_str = str(actor_id) if actor_id else None

    row_hash = compute_audit_hash(
        prev_hash=prev_hash,
        actor_id=actor_str,
        actor_role=actor_role,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_hash=ip_hash,
        detail_json=detail_json,
    )

    entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_hash=ip_hash,
        detail_json=detail_json,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "audit_entry_created",
        action=action,
        object_type=object_type,
        object_id=object_id,
        row_hash=row_hash,
    )
    return entry


async def verify_audit_chain(db: AsyncSession) -> tuple[bool, int, Optional[str]]:
    """Walk the audit chain from genesis to tip, verifying all cryptographic links.
    Returns (is_valid, verified_rows_count, error_reason).
    """
    stmt = select(AuditLog).order_by(AuditLog.created_at.asc())
    result = await db.execute(stmt)
    entries = result.scalars().all()

    if not entries:
        return True, 0, None

    expected_prev = GENESIS_HASH
    for idx, row in enumerate(entries):
        if row.prev_hash != expected_prev:
            return (
                False,
                idx,
                f"Broken chain link at row {row.id}: expected prev_hash {expected_prev}, got {row.prev_hash}",
            )

        actor_str = str(row.actor_id) if row.actor_id else None
        computed_hash = compute_audit_hash(
            prev_hash=row.prev_hash,
            actor_id=actor_str,
            actor_role=row.actor_role,
            action=row.action,
            object_type=row.object_type,
            object_id=row.object_id,
            ip_hash=row.ip_hash,
            detail_json=row.detail_json,
        )

        if computed_hash != row.row_hash:
            return (
                False,
                idx,
                f"Hash mismatch at row {row.id}: computed {computed_hash}, stored {row.row_hash}",
            )

        expected_prev = row.row_hash

    return True, len(entries), None
