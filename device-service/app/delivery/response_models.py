from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMetaModel(BaseModel):
    limit: int
    offset: int
    total: int
    has_next: bool
    order_by: list[str]


class DataResponseModel(BaseModel, Generic[T]):
    data: T


class ListResponseModel(BaseModel, Generic[T]):
    data: list[T]
    page: PageMetaModel