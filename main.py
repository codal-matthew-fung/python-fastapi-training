from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal, Optional
from models import Book, BookListResponse, BookStatsSummary
from stats import get_analytics_summary
from get_books_by_search import get_books_by_search
from get_book import get_book

# Route Logic
from list_books import list_books

# FastAPI Configuration

## Create App Instance
app = FastAPI()

## Add CORS for Frontend React App
origins = ["http://localhost:3000", "https://python-fast-api-nextjs.vercel.app/"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/books", response_model=BookListResponse)
def main(
    limit_param: int = 20,
    sort_by: Optional[Literal["ASC", "DESC"]] = None,
    sort_by_field: Optional[str] = None,
    page: Optional[int] = 1,
    custom_condition: Optional[str] = None,
):
    data = list_books(
        limit_param=limit_param,
        sort_by=sort_by,
        sort_by_field=sort_by_field,
        page=page,
        custom_condition=custom_condition,
    )

    return data


@app.get("/book/{isbn}", response_model=Book)
def get_book_data(isbn: str):
    data = get_book(isbn)
    return data


@app.get("/books/search", response_model=BookListResponse)
def search_books(
    author: Optional[str] = "",
    title: Optional[str] = "",
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    page: Optional[int] = 1,
    sort_by: Optional[Literal["ASC", "DESC"]] = None,
    sort_by_field: Optional[str] = None,
):
    data = get_books_by_search(
        author=author,
        title=title,
        min_pages=min_pages,
        max_pages=max_pages,
        page=page,
        sort_by=sort_by,
        sort_by_field=sort_by_field,
    )

    return data


@app.get("/stats/summary", response_model=BookStatsSummary)
def get_stats_summary():
    data = get_analytics_summary()

    return data
