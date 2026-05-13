from fastapi import FastAPI
from api.books import router as books_router

app = FastAPI(
    title="Library API",
    description="REST API for library book management",
    version="1.0.0",
)

app.include_router(books_router)


@app.get("/")
async def root():
    return {"message": "Library API is running"}
