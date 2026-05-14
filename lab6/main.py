from contextlib import asynccontextmanager
from fastapi import FastAPI
import database
from api.books import router as books_router
from api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield


app = FastAPI(
    title="Library API",
    description="REST API with JWT authentication and role-based authorization",
    version="6.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(books_router)


@app.get("/")
async def root():
    return {"message": "Library API is running"}
