from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.book import BookResponse
from app.schemas.user import UserResponse
from enum import IntEnum, StrEnum
from typing import Generic, TypeVar, List, Literal

T = TypeVar("T")


class PaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int


class LoanDuration(IntEnum):
    SEVEN_DAYS = 7
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30


class RenewalDuration(BaseModel):
    renewal_duration: LoanDuration


class Loan(BaseModel):
    book_id: int
    duration: LoanDuration


class LoanStatus(StrEnum):
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
    days_overdue: int = 0
    fine_amount: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class UserFineResponse(BaseModel):
    total_fines: float
    overdue_loans: list[LoanResponse]


class PaymentStatus(StrEnum):
    PAID = "paid"
    UNPAID = "unpaid"
    PENDING = "pending"
    REJECTED = "rejected"


class FinePaymentStatus(BaseModel):
    status: PaymentStatus


class VerifyPayment(BaseModel):
    action: Literal["approve", "reject"]
