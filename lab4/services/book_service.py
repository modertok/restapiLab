from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.book import BookCreate, BookStatus
from repository import book_repository


async def get_books(
    db: AsyncIOMotorDatabase,
    status: Optional[BookStatus] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return await book_repository.get_all(
        db,
        status=status.value if status is not None else None,
        author=author,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


async def get_book(db: AsyncIOMotorDatabase, book_id: str) -> Optional[dict]:
    return await book_repository.get_by_id(db, book_id)


async def add_book(db: AsyncIOMotorDatabase, book_data: BookCreate) -> dict:
    data = {
        "title": book_data.title,
        "author": book_data.author,
        "description": book_data.description,
        "status": book_data.status.value,
        "year": book_data.year,
    }
    return await book_repository.create(db, data)


async def remove_book(db: AsyncIOMotorDatabase, book_id: str) -> bool:
    return await book_repository.delete_book(db, book_id)
