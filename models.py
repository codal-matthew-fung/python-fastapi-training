from pydantic import Field, BaseModel
from typing import Optional


class Book(BaseModel):
    title: str
    authors: str
    average_rating: float
    isbn: str
    isbn13: int
    language_code: str
    num_pages: int
    ratings_count: int
    text_reviews_count: int
    publication_date: str  # Kept as str initially for easier CSV ingestion
    publisher: str


class BookMetadata(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    page_count: Optional[int] = None
    has_prev_page: Optional[bool]
    has_next_page: Optional[bool]


class BookListResponse(BaseModel):
    metadata: BookMetadata
    books: list[Book]


class TopPublisher(BaseModel):
    book_count: int
    publisher: str


class ReviewRatio(BaseModel):
    publisher: str
    total_books: int
    avg_review_ratio: float


class BookStatsSummary(BaseModel):
    top_publishers: list[TopPublisher]
    average_page_count: float
    average_rating: float
    review_ratios: list[ReviewRatio]
