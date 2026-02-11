from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from app.settings import settings


class AuthError(Exception):
    pass


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require_aud": True, "require_iss": True},
        )
        return payload
    except JWTError as e:
        raise AuthError("Invalid token") from e


def require_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except Exception as e:
        raise AuthError(f"Invalid {field}") from e