from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from sqlite3 import connect
import pandas as pd
from math import ceil
from build_query import build_book_query, BookQueryParams
from stats import get_analytics_summary
from models import Book, BookListResponse, BookStatsSummary

# Route Logic
from list_books import list_books

# FastAPI Configuration

## Create App Instance
app = FastAPI()

## Add CORS for Frontend React App
origins = ["http://localhost:3000"]
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
    sort_by: Optional[str] = None,
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
        metadata = {"total_count": 0, "total_pages": 0, "current_page": page}
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
