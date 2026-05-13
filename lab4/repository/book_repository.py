import uuid
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.book import BOOKS_COLLECTION


def _to_response(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


async def get_all(
    db: AsyncIOMotorDatabase,
    status: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    query: dict = {}
    if status is not None:
        query["status"] = status
    if author is not None:
        query["author"] = {"$regex": author, "$options": "i"}

    sort: list = [("_id", 1)]
    if sort_by == "title":
        sort = [("title", 1), ("_id", 1)]
    elif sort_by == "year":
        sort = [("year", 1), ("_id", 1)]

    col = db[BOOKS_COLLECTION]
    total = await col.count_documents(query)
    docs = await col.find(query).sort(sort).skip(offset).limit(limit).to_list(length=limit)

    return [_to_response(doc) for doc in docs], total


async def get_by_id(db: AsyncIOMotorDatabase, book_id: str) -> Optional[dict]:
    doc = await db[BOOKS_COLLECTION].find_one({"_id": book_id})
    return _to_response(doc) if doc else None


async def create(db: AsyncIOMotorDatabase, book_data: dict) -> dict:
    book_id = str(uuid.uuid4())
    await db[BOOKS_COLLECTION].insert_one({"_id": book_id, **book_data})
    return {"id": book_id, **book_data}


async def delete_book(db: AsyncIOMotorDatabase, book_id: str) -> bool:
    result = await db[BOOKS_COLLECTION].delete_one({"_id": book_id})
    return result.deleted_count > 0
