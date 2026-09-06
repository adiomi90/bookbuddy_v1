from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from app.models.loan import Loan as LoanModel
from app.schemas.analytics import TopBorrowedBookResponse, TopBorrowedBook, PendingFinesResponse, TopUnpaidUser, TopUnpaidUserResponse, MonthlyRevenueTrends, MonthlyRevenueTrendsResponse
from app.security.security import get_current_admin
from datetime import datetime, timedelta, timezone


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


@router.get("/top-unpaid-users", response_model=TopUnpaidUserResponse)
async def get_top_unpaid_user_response(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    query = select(
        UserModel.email, func.sum(LoanModel.fine_amount).label("total_unpaid")
    ).join(LoanModel, LoanModel.user_id == UserModel.id
           ).where(LoanModel.payment_status == "unpaid"
                   ).group_by(UserModel.id, UserModel.email
                              ).order_by(func.sum(LoanModel.fine_amount).desc()
                                         ).limit(5)

    result = await db.execute(query)
    top_unpaid_users = result.all()

    top_unpaid_users = [TopUnpaidUser(user=row.email, fine_total=row.total_unpaid)
                        for row in top_unpaid_users]

    return TopUnpaidUserResponse(users=top_unpaid_users)


@router.get("/monthly-revenue-trends", response_model=MonthlyRevenueTrendsResponse)
async def monthly_revenue_trends(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
    query = select(
        func.extract('year', LoanModel.payment_submitted_date).label('year'),
        func.extract('month', LoanModel.payment_submitted_date).label('month'),
        func.sum(LoanModel.fine_amount).label("total_revenue")
    ).where(
        LoanModel.payment_status == "paid",
        LoanModel.payment_submitted_date >= twelve_months_ago
    ).group_by('year', 'month'
               ).order_by('year', 'month'
                          )

    result = await db.execute(query)
    monthly_revenue = result.all()
    trending_monthly_revenue = [MonthlyRevenueTrends(
        month=f"{row.year}-{int(row.month):02d}",
        total_revenue=row.total_revenue) for row in monthly_revenue]

    return MonthlyRevenueTrendsResponse(trends=trending_monthly_revenue)
