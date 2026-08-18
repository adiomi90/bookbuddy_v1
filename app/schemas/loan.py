from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.book import BookResponse
from app.schemas.user import UserResponse
from enum import Enum


class LoanDuration(int, Enum):
    SEVEN_DAYS = 7
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30

class Loan(BaseModel):
    book_id: int
    user_id: int
    duration: LoanDuration


class LoanStatus(str, Enum):
    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"




class LoanUpdate(BaseModel):
    due_date: datetime | None = None


class LoanResponse(BaseModel):
    id: int
    user: UserResponse
    book: BookResponse
    status: LoanStatus
    due_date: datetime
    returned_date: datetime | None = None
    borrowed_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
