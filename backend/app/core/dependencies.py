"""FastAPI dependencies for tenant isolation, role-based authorization,
and authenticated session context extraction.
"""

from typing import Annotated, Optional, Callable
import uuid
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.errors import UnauthorizedException, ForbiddenException
from backend.app.core.security import decode_access_token, hash_ip
from backend.app.db.models import User, UserRole
from backend.app.db.session import get_db_session

security_bearer = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(
        self,
        user: User,
        ip_hash: str,
        request_id: Optional[str] = None,
    ):
        self.user = user
        self.user_id: uuid.UUID = user.id
        self.role: UserRole = user.role
        self.institution_id: Optional[uuid.UUID] = user.institution_id
        self.ip_hash = ip_hash
        self.request_id = request_id

    def require_tenant(self, target_institution_id: uuid.UUID) -> None:
        """Enforce strict tenant isolation. Platform admin bypasses; institution staff restricted."""
        if self.role == UserRole.PLATFORM_ADMIN:
            return
        if self.institution_id != target_institution_id:
            raise ForbiddenException(
                f"Tenant isolation breach: your account belongs to institution '{self.institution_id}', "
                f"cannot access or modify data for institution '{target_institution_id}'."
            )


async def get_client_ip_hash(request: Request) -> str:
    client_host = request.client.host if request.client else "127.0.0.1"
    return hash_ip(client_host)


async def get_current_user_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> AuthContext:
    """Dependency extracting and verifying the JWT bearer token, fetching active user."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authorization bearer token is missing.")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise UnauthorizedException("Invalid or expired authorization token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Malformed token: missing subject claim.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID in token.")

    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User associated with this token no longer exists.")

    ip_hash = await get_client_ip_hash(request)
    request_id = getattr(request.state, "request_id", None)

    return AuthContext(user=user, ip_hash=ip_hash, request_id=request_id)


def require_roles(*allowed_roles: UserRole) -> Callable[[AuthContext], AuthContext]:
    """Dependency factory checking if authenticated user possesses one of the allowed roles."""
    async def role_checker(
        ctx: AuthContext = Depends(get_current_user_context),
    ) -> AuthContext:
        if ctx.role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            raise ForbiddenException(
                f"Insufficient privileges: role '{ctx.role.value}' is not permitted. Required: {allowed_names}"
            )
        return ctx

    return role_checker
