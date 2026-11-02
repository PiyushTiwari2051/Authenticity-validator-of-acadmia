"""Authentication, TOTP, and Token Lifecycle Service."""

from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional, tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import User, RefreshToken, UserRole
from backend.app.core.security import (
    hash_password, verify_password, create_access_token,
    generate_secure_refresh_token, hash_token, generate_totp_secret,
    encrypt_secret, decrypt_secret, verify_totp, get_totp_uri
)
from backend.app.core.errors import (
    UnauthorizedException, ForbiddenException, ConflictException, NotFoundException
)
from backend.app.core.logging import logger
from backend.app.modules.audit.service import write_audit_entry

STAFF_ROLES = {UserRole.PLATFORM_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.OPERATOR}


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
    totp_code: Optional[str],
    ip_hash: str,
    user_agent: Optional[str] = None,
) -> tuple[User, str, str, bool]:
    """Authenticate credentials, check lockout, enforce TOTP for staff, rotate tokens.
    Returns (user, access_token, refresh_token, requires_totp_setup).
    """
    stmt = select(User).where(User.email == email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not user:
        # Uniform failure to prevent user enumeration
        raise UnauthorizedException("Invalid email or password.")

    # Account Lockout Check
    if user.locked_until and user.locked_until > now:
        remaining_seconds = int((user.locked_until - now).total_seconds())
        raise UnauthorizedException(f"Account temporarily locked. Retry in {remaining_seconds} seconds.")

    # Password check
    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            logger.warning("user_account_locked", email=user.email, failed_attempts=user.failed_attempts)
        await db.commit()
        raise UnauthorizedException("Invalid email or password.")

    # Reset failed attempts on valid password
    user.failed_attempts = 0
    user.locked_until = None

    # Mandatory TOTP check for staff roles
    requires_totp_setup = False
    if user.role in STAFF_ROLES:
        if not user.totp_enabled:
            requires_totp_setup = True
        else:
            if not totp_code:
                raise UnauthorizedException("Two-factor authentication code required.")
            secret = decrypt_secret(user.totp_secret_enc)
            if not verify_totp(secret, totp_code):
                raise UnauthorizedException("Invalid two-factor authentication code.")

    # Generate Access Token
    inst_str = str(user.institution_id) if user.institution_id else None
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        institution_id=inst_str,
    )

    # Generate and Store Refresh Token (Family Session)
    raw_refresh = generate_secure_refresh_token()
    token_hashed = hash_token(raw_refresh)
    family_id = uuid.uuid4()

    refresh_obj = RefreshToken(
        user_id=user.id,
        family_id=family_id,
        token_hash=token_hashed,
        expires_at=now + timedelta(days=7),
        user_agent=user_agent,
    )
    db.add(refresh_obj)

    # Audit login
    await write_audit_entry(
        db=db,
        actor_id=user.id,
        actor_role=user.role.value,
        action="user_logged_in",
        object_type="user",
        object_id=str(user.id),
        ip_hash=ip_hash,
        detail_json={"user_agent": user_agent or "unknown"},
    )

    await db.commit()
    return user, access_token, raw_refresh, requires_totp_setup


async def rotate_refresh_token(
    db: AsyncSession,
    raw_refresh_token: str,
    ip_hash: str,
    user_agent: Optional[str] = None,
) -> tuple[str, str]:
    """Rotate refresh token. Detects token reuse and instantly revokes entire session family."""
    token_hashed = hash_token(raw_refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hashed)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not token_obj:
        raise UnauthorizedException("Invalid refresh token.")

    # REUSE DETECTION: If token already revoked, someone is replaying stolen tokens!
    if token_obj.revoked_at is not None:
        # Invalidate entire family immediately
        logger.warning(
            "refresh_token_reuse_detected",
            user_id=str(token_obj.user_id),
            family_id=str(token_obj.family_id),
        )
        revoke_family_stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == token_obj.family_id)
            .values(revoked_at=now)
        )
        await db.execute(revoke_family_stmt)
        await write_audit_entry(
            db=db,
            actor_id=token_obj.user_id,
            actor_role="unknown",
            action="session_family_revoked_reuse_attack",
            object_type="refresh_token_family",
            object_id=str(token_obj.family_id),
            ip_hash=ip_hash,
            detail_json={"replayed_token_hash": token_hashed},
        )
        await db.commit()
        raise UnauthorizedException("Token reuse detected. All sessions in this family revoked.")

    if token_obj.expires_at < now:
        raise UnauthorizedException("Refresh token has expired.")

    # Fetch User
    user_stmt = select(User).where(User.id == token_obj.user_id)
    u_res = await db.execute(user_stmt)
    user = u_res.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found.")

    # Revoke current token
    token_obj.revoked_at = now

    # Issue new refresh token within same family
    new_raw_refresh = generate_secure_refresh_token()
    new_token_obj = RefreshToken(
        user_id=user.id,
        family_id=token_obj.family_id,
        token_hash=hash_token(new_raw_refresh),
        expires_at=now + timedelta(days=7),
        user_agent=user_agent,
    )
    db.add(new_token_obj)

    # Issue new access token
    inst_str = str(user.institution_id) if user.institution_id else None
    new_access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        institution_id=inst_str,
    )

    await db.commit()
    return new_access_token, new_raw_refresh
