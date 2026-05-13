from typing import Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.book import Book


async def get_all(
    db: AsyncSession,
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Book], int]:
    query = select(Book)
    count_query = select(func.count()).select_from(Book)

    if status is not None:
        query = query.where(Book.status == status)
        count_query = count_query.where(Book.status == status)

    if author is not None:
        query = query.where(Book.author.ilike(f"%{author}%"))
        count_query = count_query.where(Book.author.ilike(f"%{author}%"))

    if sort_by == "title":
        query = query.order_by(Book.title)
    elif sort_by == "year":
        query = query.order_by(Book.year)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    total_result = await db.execute(count_query)

    return list(result.scalars().all()), total_result.scalar()


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
