from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Book(BaseModel):
    title: str
    author: str
    isbn: str
    summary: str
    publisher: str
    publisher_year: int


class UpdateBook(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    summary: str | None = None


class UpdateInventory(BaseModel):
    change: int


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    summary: str
    publisher: str
    publisher_year: int
    created_at: datetime
    updated_at: datetime
    quantity: int

    model_config = ConfigDict(from_attributes=True)
