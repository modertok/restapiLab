from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.book import BookCreate, BookResponse, BookStatus, BookListResponse
from services import book_service
from database import get_db
from core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BookListResponse, status_code=200)
async def list_books(
    status: Optional[BookStatus] = Query(None),
    author: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),          # any authenticated user
):
    books, total = await book_service.get_books(
        db, status=status, author=author, sort_by=sort_by, limit=limit, offset=offset
    )
    return BookListResponse(items=books, total=total, limit=limit, offset=offset)


@router.get("/{book_id}", response_model=BookResponse, status_code=200)
async def get_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),          # any authenticated user
):
    book = await book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),             # admin only
):
    return await book_service.add_book(db, book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),             # admin only
):
    await book_service.remove_book(db, book_id)
