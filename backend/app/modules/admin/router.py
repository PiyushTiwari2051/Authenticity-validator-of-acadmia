"""Admin API Router for institution onboarding approval, suspension, and audit verification."""

from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.db.models import Institution, InstitutionStatus, UserRole, AuditLog
from backend.app.modules.institutions.schemas import InstitutionResponse
from backend.app.core.dependencies import require_roles, AuthContext
from backend.app.core.errors import NotFoundException, ConflictException
from backend.app.modules.audit.service import write_audit_entry, verify_audit_chain

router = APIRouter(prefix="/admin", tags=["Platform Admin"])


class ApproveRequest(BaseModel):
    decision_reason: str = Field(min_length=5, description="Audited human justification for approval")


class SuspendRequest(BaseModel):
    suspension_reason: str = Field(min_length=5, description="Audited justification for suspension")


@router.get("/institutions", response_model=list[InstitutionResponse])
async def list_institutions_admin(
    status_filter: Optional[InstitutionStatus] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db_session),
    ctx: AuthContext = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    """Platform Admin list institutions with status filter."""
    stmt = select(Institution)
    if status_filter:
        stmt = stmt.where(Institution.status == status_filter)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/institutions/{institution_id}/approve", response_model=InstitutionResponse)
async def approve_institution(
    institution_id: uuid.UUID,
    req: ApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    ctx: AuthContext = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    """Platform Admin manually approves an institution application."""
    stmt = select(Institution).where(Institution.id == institution_id)
    result = await db.execute(stmt)
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundException("Institution not found.")

    now = datetime.now(timezone.utc)
    inst.status = InstitutionStatus.APPROVED
    inst.approved_by = ctx.user.id
    inst.approved_at = now

    await write_audit_entry(
        db=db,
        actor_id=ctx.user.id,
        actor_role=ctx.user.role.value,
        action="institution_approved",
        object_type="institution",
        object_id=str(inst.id),
        ip_hash=ctx.ip_hash,
        detail_json={
            "institution_name": inst.name,
            "decision_reason": req.decision_reason,
            "approved_at": now.isoformat(),
        },
    )
    await db.commit()
    return inst


@router.post("/institutions/{institution_id}/suspend", response_model=InstitutionResponse)
async def suspend_institution(
    institution_id: uuid.UUID,
    req: SuspendRequest,
    db: AsyncSession = Depends(get_db_session),
    ctx: AuthContext = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    """Platform Admin suspends an institution."""
    stmt = select(Institution).where(Institution.id == institution_id)
    result = await db.execute(stmt)
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundException("Institution not found.")

    inst.status = InstitutionStatus.SUSPENDED

    await write_audit_entry(
        db=db,
        actor_id=ctx.user.id,
        actor_role=ctx.user.role.value,
        action="institution_suspended",
        object_type="institution",
        object_id=str(inst.id),
        ip_hash=ctx.ip_hash,
        detail_json={
            "institution_name": inst.name,
            "suspension_reason": req.suspension_reason,
        },
    )
    await db.commit()
    return inst


@router.get("/audit/verify")
async def verify_audit_log_endpoint(
    db: AsyncSession = Depends(get_db_session),
    ctx: AuthContext = Depends(require_roles(UserRole.PLATFORM_ADMIN)),
):
    """Verify entire audit trail cryptographic hash chain from genesis to tip."""
    is_valid, rows_count, error = await verify_audit_chain(db)
    return {
        "chain_intact": is_valid,
        "verified_rows": rows_count,
        "error": error,
        "status": "HEALTHY" if is_valid else "CORRUPTED",
    }
