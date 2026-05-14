import uuid
from typing import Optional
from repository import book_repository


def get_books(
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return book_repository.get_all(
        status=status, author=author, sort_by=sort_by, limit=limit, offset=offset
    )


def get_book(book_id: str) -> Optional[dict]:
    return book_repository.get_by_id(book_id)


def add_book(book_data: dict) -> dict:
    book_data["id"] = str(uuid.uuid4())
    return book_repository.create(book_data)


def remove_book(book_id: str) -> bool:
    return book_repository.delete(book_id)
