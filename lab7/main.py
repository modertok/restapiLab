from contextlib import asynccontextmanager
from fastapi import FastAPI
import database
from redis_client import connect_redis, close_redis
from api.books import router as books_router
from api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    await connect_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Library API",
    description="REST API with JWT auth, RBAC, and Redis rate limiting",
    version="7.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(books_router)


@app.get("/")
async def root():
    return {"message": "Library API is running"}
