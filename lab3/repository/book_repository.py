import json
import base64
from typing import Optional
from sqlalchemy import select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.book import Book


def encode_cursor(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Raises ValueError if the cursor string is not valid."""
    try:
        decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        if not isinstance(decoded, dict):
            raise ValueError
        return decoded
    except Exception:
        raise ValueError("Invalid cursor")


async def get_all_cursor(
    db: AsyncSession,
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> tuple[list[Book], Optional[str]]:
    cursor_data = decode_cursor(cursor) if cursor else {}

    query = select(Book)

    if status is not None:
        query = query.where(Book.status == status)

    if author is not None:
        query = query.where(Book.author.ilike(f"%{author}%"))

    # Apply cursor condition and ordering based on sort field
    if sort_by == "title":
        if cursor_data:
            ct = cursor_data.get("title", "")
            ci = cursor_data.get("id", "")
            query = query.where(
                or_(Book.title > ct, and_(Book.title == ct, Book.id > ci))
            )
        query = query.order_by(Book.title, Book.id)
    elif sort_by == "year":
        if cursor_data:
            cy = cursor_data.get("year", 0)
            ci = cursor_data.get("id", "")
            query = query.where(
                or_(Book.year > cy, and_(Book.year == cy, Book.id > ci))
            )
        query = query.order_by(Book.year, Book.id)
    else:
        if cursor_data:
            query = query.where(Book.id > cursor_data.get("id", ""))
        query = query.order_by(Book.id)

    # Fetch one extra item to detect whether a next page exists
    result = await db.execute(query.limit(limit + 1))
    books = list(result.scalars().all())

    has_next = len(books) > limit
    if has_next:
        books = books[:limit]

    next_cursor: Optional[str] = None
    if has_next and books:
        last = books[-1]
        if sort_by == "title":
            next_cursor = encode_cursor({"title": last.title, "id": last.id})
        elif sort_by == "year":
            next_cursor = encode_cursor({"year": last.year, "id": last.id})
        else:
            next_cursor = encode_cursor({"id": last.id})

    return books, next_cursor


async def get_by_id(db: AsyncSession, book_id: str) -> Optional[Book]:
    result = await db.execute(select(Book).where(Book.id == book_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, book_data: dict) -> Book:
    book = Book(**book_data)
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: str) -> bool:
    result = await db.execute(delete(Book).where(Book.id == book_id))
    await db.commit()
    return result.rowcount > 0
