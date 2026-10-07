from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List
from datetime import datetime


class ReservationCreate(BaseModel):
    isbn: Optional[str] = None
    title: Optional[str] = None

    @model_validator(mode="after")
    def check_isbn_or_title(self):
        if not self.isbn and not self.title:
            raise ValueError("Either 'isbn' or 'title' must be provided")
        return self


class ReservationResponse(BaseModel):
    id: int
    book_id: int
    book_title: str
    status: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReservationListResponse(BaseModel):
    reservations: List[ReservationResponse]


class ReservationCancelRequest(BaseModel):
    note: str


class ReservationCancelResponse(BaseModel):
    id: int
    book_title: str
    user_email: str
    status: str
    cancelled_at: datetime
    note: str

    model_config = ConfigDict(from_attributes=True)


class ReservationApproveResponse(BaseModel):
    id: int
    book_title: str
    user_email: str
    status: str
    expires_at: datetime
    message: str

    model_config = ConfigDict(from_attributes=True)
