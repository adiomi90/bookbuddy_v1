from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.models.user import User


class TopBorrowedBook(BaseModel):
    book_title: str
    borrow_count: int


class TopBorrowedBookResponse(BaseModel):
    books: List[TopBorrowedBook]


class PendingFinesResponse(BaseModel):
    total_pending_amount: float


class TopUnpaidUser(BaseModel):
    user_email: EmailStr
    total_unpaid: float


class TopUnpaidUserResponse(BaseModel):
    users: List[TopUnpaidUser]
