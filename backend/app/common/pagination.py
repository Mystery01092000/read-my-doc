from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PaginationParams) -> "PaginatedResponse[T]":
        pages = (total + params.limit - 1) // params.limit
        return cls(items=items, total=total, page=params.page, limit=params.limit, pages=pages)
