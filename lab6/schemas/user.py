from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
