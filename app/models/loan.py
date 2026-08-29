from sqlalchemy import String, DateTime, func, ForeignKey, CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base
from app.models.book import Book


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="borrowed")
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    renewal_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False)
    returned_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    borrowed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                    server_default=func.now(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="loans")
    book: Mapped["Book"] = relationship(back_populates="loans")

    __table_args__ = (
        CheckConstraint(
            "status IN ('borrowed', 'returned', 'overdue')",
            name="check_loan_status_valid"
        ),
    )
