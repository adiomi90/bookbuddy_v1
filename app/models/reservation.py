from sqlalchemy import String, DateTime, func, ForeignKey, CheckConstraint, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base
from app.models.book import Book


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending")
    cancellation_note: Mapped[str | None] = mapped_column(
        String(500), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())

    user: Mapped["User"] = relationship(
        back_populates="reservations")  # type: ignore
    book: Mapped["Book"] = relationship(back_populates="reservations")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'ready', 'expired', 'cancelled','picked_up')",
            name="check_reservation_status"
        ),
    )
