from typing import List, Dict, Optional
from models.book import books_db


async def get_all() -> List[Dict]:
    return list(books_db)


async def get_by_id(book_id: str) -> Optional[Dict]:
    for book in books_db:
        if book["id"] == book_id:
            return book
    return None


async def create(book_data: Dict) -> Dict:
    books_db.append(book_data)
    return book_data


async def delete(book_id: str) -> bool:
    for i, book in enumerate(books_db):
        if book["id"] == book_id:
            books_db.pop(i)
            return True
    return False
