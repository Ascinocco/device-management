from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    tenant_id: UUID
    user_id: UUID


class BaseAppException(Exception):
    pass


class ValidationError(BaseAppException):
    pass


class NotFoundError(BaseAppException):
    pass


class ConflictError(BaseAppException):
    pass


T = TypeVar("T")


@dataclass(frozen=True)
class PageMeta:
    limit: int
    offset: int
    total: int
    has_next: bool
    order_by: list[str]


@dataclass(frozen=True)
class DataResponse(Generic[T]):
    data: T


@dataclass(frozen=True)
class ListResponse(Generic[T]):
    data: list[T]
    page: PageMeta