from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.book import BookResponse
from app.schemas.user import UserResponse
from enum import Enum


class Loan(BaseModel):
    book_id: int
    due_date: datetime


class LoanStatus(str, Enum):
    borrowed = "borrowed"
    returned = "returned"
    overdue = "overdue"


class LoanUpdate(BaseModel):
    due_date: datetime | None = None


class LoanResponse(BaseModel):
    id: int
    user: UserResponse
    book: BookResponse
    status: str
    due_date: datetime
    returned_date: datetime | None = None
    borrowed_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
