from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    year: Mapped[int] = mapped_column(Integer, nullable=False)
