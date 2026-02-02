from fastapi import HTTPException
import pandas as pd
from typing import Optional
from sqlite3 import connect
from math import ceil
from build_query import build_book_query, BookQueryParams


def list_books(
    limit_param: int = 20,
    sort_by: Optional[str] = None,
    sort_by_field: Optional[str] = None,
    page: Optional[int] = 1,
    custom_condition: Optional[str] = None,
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
    params_model = BookQueryParams(
        sort_by=sort_by,
        sort_by_field=sort_by_field,
        custom_condition=custom_condition,
        page=page,
        limit=limit_param,
    )
    # Build the SQL query dynamically based on parameters
    query, params = build_book_query(book_params=params_model)
    print("QUERYING BY:", query)
    books_df = pd.read_sql_query(query, conn, params=params)
    try:
        data = books_df.to_dict(orient="records")

        query_with_count, params = build_book_query(
            book_params=params_model, with_count=True
        )
        df = pd.read_sql_query(query_with_count, conn, params=params)
        metadata = {
            "metadata": {
                "total_count": 0,
                "total_pages": 0,
                "current_page": page,
                "page_count": 20,
            }
        }
        if df.empty:
            return {
                "metadata": {
                    "total_count": 0,
                    "total_pages": 0,
                    "current_page": page,
                    "page_count": 20,
                },
                "books": [],
            }

        total = df["total"][0]
        if total > 0:
            metadata = {
                "metadata": {
                    "total_count": int(total),
                    # Given integer division, need to get float and then ceil to get total pages
                    # e.g., 45/20 = 2.25 -> ceil(2.25) = 3 pages
                    "total_pages": ceil(total / limit_param),
                    "current_page": page,
                    "page_count": len(data),
                }
            }

        response_data = {
            "metadata": metadata["metadata"],
            "books": data,
        }

        conn.close()

        return response_data
    # Handle exceptions from database operations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
