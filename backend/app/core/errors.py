"""Standard RFC 9457 Problem Details error classes and FastAPI exception handlers."""

from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class SanadException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        title: str,
        detail: str,
        invalid_params: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.invalid_params = invalid_params or []


class UnauthorizedException(SanadException):
    def __init__(self, detail: str = "Authentication required or token expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            title="Authentication Failed",
            detail=detail,
        )


class ForbiddenException(SanadException):
    def __init__(self, detail: str = "Access forbidden for this role or tenant"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            title="Permission Denied",
            detail=detail,
        )


class NotFoundException(SanadException):
    def __init__(self, detail: str = "The requested resource was not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            title="Resource Not Found",
            detail=detail,
        )


class ConflictException(SanadException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            title="Resource Conflict",
            detail=detail,
        )


async def sanad_exception_handler(request: Request, exc: SanadException) -> JSONResponse:
    """Format exceptions according to RFC 9457 Application/Problem+JSON."""
    request_id = getattr(request.state, "request_id", None)
    content: dict[str, Any] = {
        "type": f"https://sanad.local/errors/{exc.code.lower()}",
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "code": exc.code,
        "instance": request.url.path,
    }
    if request_id:
        content["request_id"] = request_id
    if exc.invalid_params:
        content["invalid_params"] = exc.invalid_params

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"Content-Type": "application/problem+json"},
    )
