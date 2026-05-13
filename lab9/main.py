from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy import func, select

import database
from api.books import router as books_router
from models.book import Book

# ── Sample data for load testing ────────────────────────────────────────────

_TITLES = [
    "Kobzar", "Eneyida", "Lisova pisnia", "Tini zabutykh predkiv",
    "Intermezzo", "Zemlia", "Pryimachka", "Bur'yan", "Vovchykha",
    "Kaidasheva simia",
]
_AUTHORS = [
    "Taras Shevchenko", "Ivan Kotlyarevsky", "Lesia Ukrainka",
    "Mykhailo Kotsiubynsky", "Ivan Nechui-Levytsky", "Panas Myrny",
]


async def _seed_books() -> None:
    """Insert 200 books on first startup so load tests have realistic data."""
    async with database.AsyncSessionLocal() as session:
        count = (await session.execute(
            select(func.count()).select_from(Book)
        )).scalar()
        if count > 0:
            return
        books = [
            Book(
                id=str(uuid4()),
                title=f"{_TITLES[i % len(_TITLES)]} — том {i + 1}",
                author=_AUTHORS[i % len(_AUTHORS)],
                description=f"Sample book #{i + 1} for load testing",
                status="available" if i % 4 != 0 else "issued",
                year=1800 + (i % 200),
            )
            for i in range(200)
        ]
        session.add_all(books)
        await session.commit()


# ── App ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    await _seed_books()
    yield


app = FastAPI(
    title="Library API — Load Test Target",
    description="GET /books/ endpoint for Locust load testing",
    version="9.0.0",
    lifespan=lifespan,
)

app.include_router(books_router)


@app.get("/")
async def root():
    return {"message": "Library API is running"}
