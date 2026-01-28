from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from sqlite3 import connect
import pandas as pd
from math import ceil
from build_query import build_book_query, BookQueryParams
from stats import get_analytics_summary

# FastAPI Configuration

## Create App Instance
app = FastAPI()

## Add CORS for Frontend React App
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allows_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


class Book(BaseModel):
    bookID: Optional[int] = Field(default=None, primary_key=True)
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


class BookListResponse(BaseModel):
    metadata: BookMetadata
    books: list[Book]


"""
top_publishers": [],
        "average_page_count": 0,
        "average_rating": 0.0,
        "review_ratios": [],
"""


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


@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/books", response_model=BookListResponse)
def list_items(
    limit_param: int = 20,
    isbn: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_by_field: Optional[str] = None,
    page: Optional[int] = 1,
):
    conn = connect("books.db")
    # If the connection fails, raise an HTTPException
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    if limit_param > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit parameter cannot exceed 100.",
        )
    # Build the SQL query dynamically based on parameters
    query = "SELECT * FROM books"
    condition = ""
    sort = ""
    limit = f"LIMIT {limit_param}"
    offset = f"OFFSET {(page - 1) * limit_param}"
    if isbn:
        condition += f" isbn='{isbn}'"
    if sort_by and sort_by_field:
        sort = f"ORDER BY {sort_by_field} {sort_by}"
    if condition:
        condition = "WHERE" + condition
    query += f" {condition} {sort} {limit} {offset};"
    try:
        df = pd.read_sql_query(query, conn)
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No books found with the given criteria.",
            )

        total = pd.read_sql_query(
            f"SELECT COUNT(*) as total FROM books {condition}", conn
        )
        tot = total["total"][0]
        if tot > 0:
            print(tot)
            metadata = {
                "metadata": {
                    "total_count": int(tot),
                    # Given integer division, need to get float and then ceil to get total pages
                    # e.g., 45/20 = 2.25 -> ceil(2.25) = 3 pages
                    "total_pages": ceil(tot / limit_param),
                    "current_page": page,
                }
            }
            print(metadata)

        data = df.to_dict(orient="records")
        reponse_data = {
            "metadata": metadata["metadata"],
            "books": data,
        }

        conn.close()
    # Handle exceptions from database operations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return reponse_data


@app.get("/book/{isbn}", response_model=Book)
def get_book(isbn: str):
    conn = connect("books.db")
    isbn = str(isbn)
    query = f'SELECT * FROM books WHERE isbn="{isbn}";'
    try:
        df = pd.read_sql_query(query, conn)
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="Book not found.",
            )
        item = df.to_dict(orient="records")[0]
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return item


@app.get("/books/search", response_model=BookListResponse)
def search_books(
    author: Optional[str] = "",
    title: Optional[str] = "",
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    page: Optional[int] = 1,
):
    conn = connect("books.db")
    params_model = BookQueryParams(
        author=f"%{author}%" if author else None,
        title=f"%{title}%" if title else None,
        min_pages=min_pages,
        max_pages=max_pages,
        page=page,
    )
    print(params_model.model_dump())
    query, params = build_book_query(params_model)

    print(f"Query: {query}")
    print(f"Params: {params}")

    try:
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {
                "metadata": {"total_count": 0, "total_pages": 0, "current_page": page},
                "books": [],
            }
        count_query, count_params = build_book_query(params_model, with_count=True)
        total = pd.read_sql_query(count_query, conn, params=count_params)

        data = df.to_dict(orient="records")

        tot = total["total"][0]
        if tot > 0:
            metadata = {
                "metadata": {
                    "total_count": int(tot),
                    "page_count": int(len(data)),
                    # Given integer division, need to get float and then ceil to get total pages
                    # e.g., 45/20 = 2.25 -> ceil(2.25) = 3 pages
                    "total_pages": ceil(tot / 20),
                    "current_page": page,
                }
            }
            print(metadata)

        response_data = {
            "metadata": metadata["metadata"],
            "books": data,
        }
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response_data


@app.get("/stats/summary", response_model=BookStatsSummary)
def get_stats_summary():
    data = get_analytics_summary()

    return data
