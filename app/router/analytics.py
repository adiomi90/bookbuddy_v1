from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from app.models.loan import Loan as LoanModel
from app.schemas.analytics import TopBorrowedBookResponse, TopBorrowedBook, PendingFinesResponse
from app.security.security import get_current_admin


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/top-borrowed-books", response_model=TopBorrowedBookResponse)
async def get_top_borrowed_books(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    query = select(
        BookModel.title,
        func.count(LoanModel.id).label("borrow_count")
    ).join(
        LoanModel, BookModel.id == LoanModel.book_id
    ).group_by(
        BookModel.id, BookModel.title
    ).order_by(
        func.count(LoanModel.id).desc()
    ).limit(5)

    result = await db.execute(query)

    rows = result.all()

    top_books = [
        TopBorrowedBook(book_title=row.title, borrow_count=row.borrow_count)
        for row in rows
    ]

    return TopBorrowedBookResponse(books=top_books)


@router.get("/pending-fines-total", response_model=PendingFinesResponse)
async def get_peding_fines_total(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    query = select(
        func.sum(LoanModel.fine_amount)
    ).where(LoanModel.payment_status == "pending")

    result = await db.execute(query)
    total = result.scalar_one_or_none()

    final_total = total if total else 0.0

    return PendingFinesResponse(total_pending_amount=final_total)
