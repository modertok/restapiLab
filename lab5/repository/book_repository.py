from typing import Optional
from models.book import books_db


def get_all(
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    result = list(books_db)

    if status is not None:
        result = [b for b in result if b["status"] == status]

    if author is not None:
        result = [b for b in result if author.lower() in b["author"].lower()]

    if sort_by == "title":
        result.sort(key=lambda b: b["title"].lower())
    elif sort_by == "year":
        result.sort(key=lambda b: b["year"])

    total = len(result)
    return result[offset: offset + limit], total


def get_by_id(book_id: str) -> Optional[dict]:
    for book in books_db:
        if book["id"] == book_id:
            return book
    return None


def create(book_data: dict) -> dict:
    books_db.append(book_data)
    return book_data


def delete(book_id: str) -> bool:
    for i, book in enumerate(books_db):
        if book["id"] == book_id:
            books_db.pop(i)
            return True
    return False
