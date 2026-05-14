import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.book import BookCreate, BookStatus
from repository import book_repository
from models.book import Book


async def get_books(
    db: AsyncSession,
    status: Optional[BookStatus] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> tuple[list[Book], Optional[str]]:
    return await book_repository.get_all_cursor(
        db,
        status=status.value if status is not None else None,
        author=author,
        sort_by=sort_by,
        cursor=cursor,
        limit=limit,
    )


async def get_book(db: AsyncSession, book_id: str) -> Optional[Book]:
    return await book_repository.get_by_id(db, book_id)


async def add_book(db: AsyncSession, book_data: BookCreate) -> Book:
    book_dict = {
        "id": str(uuid.uuid4()),
        "title": book_data.title,
        "author": book_data.author,
        "description": book_data.description,
        "status": book_data.status.value,
        "year": book_data.year,
    }
    return await book_repository.create(db, book_dict)


async def remove_book(db: AsyncSession, book_id: str) -> bool:
    return await book_repository.delete_book(db, book_id)
