from sqlite3 import connect
import pandas as pd


def load_data():
    books = pd.read_csv("data/books.csv", sep=",", header=0, skip_blank_lines=True)

    conn = connect("books.db")

    books.to_sql("books", conn, if_exists="replace", index=False)

    print(books.head())

    conn.close()

    return


def main():
    load_data()
    return


if __name__ == "__main__":
    main()
