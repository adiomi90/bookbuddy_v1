from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Book(BaseModel):
    title: str
    author: str
    isbn: str
    summary: str


class UpdateBook(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    summary: str | None = None


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    summary: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
