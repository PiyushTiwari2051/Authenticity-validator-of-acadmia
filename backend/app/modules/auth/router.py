"""Authentication and Identity API Router."""

from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.modules.auth.schemas import (
    LoginRequest, LoginResponse, TOTPEnrollResponse, TOTPVerifyRequest, RefreshTokenRequest
)
from backend.app.modules.auth.service import authenticate_user, rotate_refresh_token
from backend.app.core.dependencies import get_client_ip_hash, get_current_user_context, AuthContext
from backend.app.core.security import generate_totp_secret, encrypt_secret, decrypt_secret, verify_totp, get_totp_uri
from backend.app.core.errors import UnauthorizedException, ForbiddenException
from backend.app.modules.audit.service import write_audit_entry

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    ip_hash: str = Depends(get_client_ip_hash),
):
    user_agent = request.headers.get("User-Agent")
    user, access_token, refresh_token, requires_totp_setup = await authenticate_user(
        db=db,
        email=req.email,
        password=req.password,
        totp_code=req.totp_code,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )

    # Set httpOnly Secure SameSite cookie for the refresh token
    response.set_cookie(
        key="sanad_refresh",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth",
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=900,
        role=user.role,
        institution_id=user.institution_id,
        requires_totp_setup=requires_totp_setup,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    response: Response,
    body: RefreshTokenRequest = None,
    db: AsyncSession = Depends(get_db_session),
    ip_hash: str = Depends(get_client_ip_hash),
):
    # Read refresh token from either cookie or JSON body
    token = request.cookies.get("sanad_refresh")
    if not token and body:
        token = body.refresh_token

    if not token:
        raise UnauthorizedException("Refresh token is required.")

    user_agent = request.headers.get("User-Agent")
    new_access_token, new_refresh_token = await rotate_refresh_token(
        db=db,
        raw_refresh_token=token,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )

    response.set_cookie(
        key="sanad_refresh",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth",
    )

    return LoginResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in_seconds=900,
        role="unknown",  # client reads actual role from JWT claims
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="sanad_refresh", path="/api/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/totp/enroll", response_model=TOTPEnrollResponse)
async def totp_enroll(
    ctx: AuthContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Initiate TOTP enrollment for staff roles."""
    secret = generate_totp_secret()
    # Save encrypted secret temporarily
    ctx.user.totp_secret_enc = encrypt_secret(secret)
    await db.commit()

    uri = get_totp_uri(secret=secret, email=ctx.user.email)
    return TOTPEnrollResponse(totp_secret=secret, provisioning_uri=uri)


@router.post("/totp/verify")
async def totp_verify(
    req: TOTPVerifyRequest,
    ctx: AuthContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Verify enrollment TOTP code and permanently activate 2FA."""
    if not ctx.user.totp_secret_enc:
        raise ForbiddenException("TOTP enrollment has not been initiated.")

    secret = decrypt_secret(ctx.user.totp_secret_enc)
    if not verify_totp(secret, req.totp_code):
        raise UnauthorizedException("Invalid TOTP verification code.")

    ctx.user.totp_enabled = True
    await write_audit_entry(
        db=db,
        actor_id=ctx.user.id,
        actor_role=ctx.user.role.value,
        action="totp_two_factor_activated",
        object_type="user",
        object_id=str(ctx.user.id),
        ip_hash=ctx.ip_hash,
        detail_json={},
    )
    await db.commit()
    return {"status": "success", "detail": "Two-factor authentication successfully enabled."}
