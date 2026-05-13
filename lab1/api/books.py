from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from schemas.book import BookCreate, BookResponse, BookStatus
from services import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[BookResponse], status_code=200)
async def list_books(
    status: Optional[BookStatus] = Query(None, description="Filter by book status"),
    author: Optional[str] = Query(None, description="Filter by author name (partial, case-insensitive)"),
    sort_by: Optional[str] = Query(None, pattern="^(title|year)$", description="Sort by: title or year"),
):
    return await book_service.get_books(status=status, author=author, sort_by=sort_by)


@router.get("/{book_id}", response_model=BookResponse, status_code=200)
async def get_book(book_id: str):
    book = await book_service.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreate):
    return await book_service.add_book(book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: str):
    await book_service.remove_book(book_id)
    # Idempotent: always 204 regardless of whether the book existed
