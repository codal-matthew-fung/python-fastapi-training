from sqlite3 import connect
import pandas as pd
from fastapi import HTTPException


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
