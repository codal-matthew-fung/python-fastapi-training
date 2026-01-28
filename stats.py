from sqlite3 import connect
import pandas as pd
from fastapi import HTTPException
from watermark import watermark
import json


def get_analytics(conn):
    stats = {
        "top_publishers": [],
        "average_page_count": 0,
        "average_rating": 0.0,
        "review_ratios": [],
    }
    # Calculate the top 5 publishers by book count
    query = """
    SELECT
        COUNT(publisher) AS book_count,
        publisher
    FROM books
    GROUP BY publisher
    ORDER BY book_count DESC
    LIMIT 5
    """
    try:
        df = pd.read_sql_query(query, conn)
        top_publishers = df.to_dict(orient="records")
        print(f"Top Publishers: {top_publishers}")
        stats["top_publishers"] = top_publishers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Calculate the average page count and rating across the entire dataset
    query = """
    SELECT
        ROUND(AVG(num_pages), 0) as avg_page_count,
        ROUND(AVG(average_rating), 2) as avg_rating
    FROM books
    """
    try:
        df = pd.read_sql_query(query, conn)
        averages = df.to_dict(orient="records")[0]
        print(f"Averages: {averages}")
        stats["average_page_count"] = averages["avg_page_count"]
        stats["average_rating"] = averages["avg_rating"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    query = """
    SELECT 
        publisher, 
        COUNT(*) as total_books,
        ROUND(AVG(text_reviews_count * 1.0 / NULLIF(ratings_count, 0)), 2) AS avg_review_ratio
    FROM books
    WHERE ratings_count > 0
    GROUP BY publisher
    HAVING total_books > 5
    ORDER BY avg_review_ratio DESC
    LIMIT 5;
    """
    try:
        df = pd.read_sql_query(query, conn)
        review_ratios = df.to_dict(orient="records")
        stats["review_ratios"] = review_ratios

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    print(stats)

    return stats


def get_analytics_summary():
    conn = connect("books.db")

    # Create a cache table if it doesn't exist
    query = """
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data TEXT,                            
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    conn.execute(query)

    cursor = conn.cursor()
    cursor.execute("SELECT data FROM analytics_cache WHERE id = 1")
    row = cursor.fetchone()

    if not row:
        print(f"CALCULATING THE STATS, Row is: {row}")
        # Calculate if the cache is empty
        stats = get_analytics(conn=conn)
        stats_json = json.dumps(stats)
        query = """
        INSERT INTO analytics_cache (id, data, last_updated)
        VALUES (1, :stats_json, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            data = excluded.data,
            last_updated = excluded.last_updated;
        """
        conn.execute(query, {"stats_json": stats_json})
        conn.commit()

        return stats
    else:
        print("Retrieved the stats from the analytics_cache table.")
        data = json.loads(row[0])

        return data
