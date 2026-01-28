import sqlite3
import pandas as pd


def query_db(query="SELECT * FROM products LIMIT 5;"):
    query = input("Enter your SQL query: ")
    conn = sqlite3.connect("books.db")
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()
    return df


if __name__ == "__main__":
    query_db()
