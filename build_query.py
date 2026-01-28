from pydantic import BaseModel
from typing import Optional, Literal

accepted_fields = Literal[
    "bookID",
    "title",
    "authors",
    "average_rating",
    "isbn",
    "isbn13",
    "language_code",
    "num_pages",
    "ratings_count",
    "text_reviews_count",
    "publication_date",
    "publisher",
]


class BookQueryParams(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    min_pages: Optional[int] = None
    max_pages: Optional[int] = None
    page: int = 1
    limit: int = 20
    offset: int = 0
    sort_by: Optional[Literal["ASC", "DESC"]] = "ASC"
    sort_by_field: Optional[accepted_fields] = "bookID"
    custom_condition: Optional[str] = None


def build_book_query(book_params: BookQueryParams, with_count: bool = False):
    query = "SELECT * FROM books"
    if with_count:
        query = "SELECT COUNT(*) as total FROM books"
    conditions = []
    params = BookQueryParams()
    if not book_params.custom_condition:
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
    else:
        conditions.append(":custom_condition")
        # TODO: Fix the parsing of custom conditions
        print(f"Custom Condition: {book_params.custom_condition}")
        params.custom_condition = book_params.custom_condition

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if params.offset > 0:
        offset = (book_params.page - 1) * book_params.limit
        params.offset = offset
    if not with_count:
        query += " LIMIT :limit OFFSET :offset;"

    print(query)
    return query, params.model_dump()
