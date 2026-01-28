from pydantic import BaseModel
from typing import Optional


class BookQueryParams(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    min_pages: Optional[int] = None
    max_pages: Optional[int] = None
    page: int = 1
    limit: int = 20
    offset: int = 0


def build_book_query(book_params: BookQueryParams, with_count: bool = False):
    query = "SELECT * FROM books"
    if with_count:
        query = "SELECT COUNT(*) as total FROM books"
    conditions = []
    params = BookQueryParams()

    if book_params.author:
        conditions.append("authors LIKE :author")
        params.author = book_params.author

    if book_params.title:
        conditions.append("title LIKE :title")
        params.title = book_params.title

    if book_params.min_pages is not None:
        conditions.append("num_pages >= :min_pages")
        params.min_pages = book_params.min_pages

    if book_params.max_pages is not None:
        conditions.append("num_pages <= :max_pages")
        params.max_pages = book_params.max_pages

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if params.offset > 0:
        offset = (book_params.page - 1) * book_params.limit
        params.offset = offset
    if not with_count:
        query += " LIMIT :limit OFFSET :offset;"

    return query, params.model_dump()
