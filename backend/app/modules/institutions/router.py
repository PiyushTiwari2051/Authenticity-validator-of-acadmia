"""Institution API Router for onboarding, lifecycle, and public status."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.db.models import Institution, InstitutionStatus, InstitutionKey, KeyStatus, UserRole
from backend.app.modules.institutions.schemas import (
    InstitutionApplyRequest, InstitutionResponse, InstitutionPublicResponse
)
from backend.app.core.dependencies import get_current_user_context, require_roles, AuthContext
from backend.app.core.errors import ConflictException, NotFoundException, ForbiddenException
from backend.app.modules.audit.service import write_audit_entry

router = APIRouter(tags=["Institutions"])


@router.post("/institutions/apply", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def apply_institution(
    req: InstitutionApplyRequest,
    db: AsyncSession = Depends(get_db_session),
    ctx: AuthContext = Depends(get_current_user_context),
):
    """Submit an institution application for platform review."""
    # Check registration number or domain conflicts
    stmt = select(Institution).where(
        (Institution.registration_no == req.registration_no) |
        (Institution.official_domain == req.official_domain.lower().strip())
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException("An institution with this registration number or official domain already exists.")

    inst = Institution(
        name=req.name.strip(),
        type=req.type.strip(),
        state=req.state.strip(),
        registration_no=req.registration_no.strip(),
        official_domain=req.official_domain.lower().strip(),
        status=InstitutionStatus.PENDING,
    )
    db.add(inst)
    await db.flush()

    # If the applying user had no institution bound, associate them as applicant
    if not ctx.user.institution_id:
        ctx.user.institution_id = inst.id

    await write_audit_entry(
        db=db,
        actor_id=ctx.user.id,
        actor_role=ctx.user.role.value,
        action="institution_applied",
        object_type="institution",
        object_id=str(inst.id),
        ip_hash=ctx.ip_hash,
        detail_json={"name": inst.name, "domain": inst.official_domain},
    )
    await db.commit()
    return inst


@router.get("/institutions/{institution_id}/public", response_model=InstitutionPublicResponse)
async def get_institution_public(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Publicly inspect institution metadata, official status, and registered active key fingerprints."""
    stmt = select(Institution).where(Institution.id == institution_id)
    result = await db.execute(stmt)
    inst = result.scalar_one_or_none()
    if not inst:
        raise NotFoundException("Institution not found.")

    # Fetch active keys
    k_stmt = select(InstitutionKey.key_id).where(
        InstitutionKey.institution_id == institution_id,
        InstitutionKey.status == KeyStatus.ACTIVE,
    )
    k_res = await db.execute(k_stmt)
    active_keys = list(k_res.scalars().all())

    return InstitutionPublicResponse(
        id=inst.id,
        name=inst.name,
        type=inst.type,
        state=inst.state,
        official_domain=inst.official_domain,
        status=inst.status,
        approved_at=inst.approved_at,
        active_key_ids=active_keys,
    )
