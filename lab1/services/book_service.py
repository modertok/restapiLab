import uuid
from typing import List, Dict, Optional
from schemas.book import BookCreate, BookStatus
from repository import book_repository


async def get_books(
    status: Optional[BookStatus] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
) -> List[Dict]:
    books = await book_repository.get_all()

    if status is not None:
        books = [b for b in books if b["status"] == status.value]

    if author is not None:
        books = [b for b in books if author.lower() in b["author"].lower()]

    if sort_by == "title":
        books = sorted(books, key=lambda b: b["title"].lower())
    elif sort_by == "year":
        books = sorted(books, key=lambda b: b["year"])

    return books


async def get_book(book_id: str) -> Optional[Dict]:
    return await book_repository.get_by_id(book_id)


async def add_book(book_data: BookCreate) -> Dict:
    book_dict = {
        "id": str(uuid.uuid4()),
        **book_data.model_dump(),
    }
    return await book_repository.create(book_dict)


async def remove_book(book_id: str) -> bool:
    return await book_repository.delete(book_id)
