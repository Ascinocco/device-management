from fastapi import Header

from app.contracts import RequestContext
from app.settings import settings
from infra.security.jwt import AuthError, require_uuid


def get_request_context(
    x_tenant_id: str | None = Header(default=None, alias="x-tenant-id"),
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
    x_internal_token: str | None = Header(default=None, alias="x-internal-token"),
) -> RequestContext:
    if not x_internal_token or x_internal_token != settings.device_service_token:
        raise AuthError("Invalid internal token")
    if not x_tenant_id or not x_user_id:
        raise AuthError("Missing internal identity headers")
    return RequestContext(
        tenant_id=require_uuid(x_tenant_id, "tenant_id"),
        user_id=require_uuid(x_user_id, "user_id"),
    )