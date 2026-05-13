from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class BookStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: BookStatus = BookStatus.AVAILABLE
    year: int = Field(..., ge=1000, le=2100)


class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    items: List[BookResponse]
    total: int
    limit: int
    offset: int
