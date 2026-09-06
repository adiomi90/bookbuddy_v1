from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.models.user import User
from datetime import date


class TopBorrowedBook(BaseModel):
    book_title: str
    borrow_count: int


class TopBorrowedBookResponse(BaseModel):
    books: List[TopBorrowedBook]


class PendingFinesResponse(BaseModel):
    total_pending_amount: float


class TopUnpaidUser(BaseModel):
    user: EmailStr
    fine_total: float


class TopUnpaidUserResponse(BaseModel):
    users: List[TopUnpaidUser]


class MonthlyRevenueTrends(BaseModel):
    month: str
    total_revenue: float


class MonthlyRevenueTrendsResponse(BaseModel):
    trends: List[MonthlyRevenueTrends]
