from fastapi import HTTPException
from math import ceil
from sqlite3 import connect
from build_query import BookQueryParams, build_book_query
import pandas as pd
from typing import Optional


def get_books_by_search(
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

        response_data = {
            "metadata": metadata["metadata"],
            "books": data,
        }
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response_data
