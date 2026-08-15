from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.loan import Loan, LoanResponse, LoanUpdate
from app.models.loan import Loan as LoanModel
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from datetime import datetime


router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=LoanResponse)
async def create_loan(loan: Loan, db: AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(UserModel).where(UserModel.id == loan.user_id))
    user_result = user_query.scalar_one_or_none()

    if not user_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {loan.user_id} does not exist"
        )
    book_query = await db.execute(select(BookModel).where(BookModel.id == loan.book_id))
    book_result = book_query.scalar_one_or_none()

    if not book_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {loan.book_id} does not exist"
        )
    if book_result.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient book in stock for book {loan.book_id}"
        )

    existing_loan = await db.execute(select(LoanModel)
                                     .where(
        LoanModel.user_id == loan.user_id,
                                     LoanModel.book_id == loan.book_id,
                                         LoanModel.status == "borrowed"
                                     )
                                     )
    existing_loan_result = existing_loan.scalar_one_or_none()

    if existing_loan_result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {loan.user_id} already has active loan for  {loan.book_id}"
        )

    book_result.quantity -= 1

    db_loan = LoanModel(
        user_id=loan.user_id,
        book_id=loan.book_id,
        due_date=loan.due_date
    )

    db.add(db_loan)
    await db.flush()

    loan_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    ).where(LoanModel.id == db_loan.id)
    )
    db_loan = loan_query.scalar_one()

    await db.commit()
    return db_loan


@router.patch("/{loan_id}/return", response_model=LoanResponse)
async def return_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    loan_query = await db.execute(select(LoanModel).where(LoanModel.id == loan_id))
    loan_query_result = loan_query.scalar_one_or_none()

    if not loan_query_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Loan with id {loan_id} was not found")

    if loan_query_result.status == "returned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Loan id {loan_id} can't be returned")

    book_query = await db.execute(select(BookModel).where(BookModel.id == loan_query_result.book_id))
    book_query_result = book_query.scalar_one_or_none()

    if not book_query_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book id {loan_query_result.book_id} can't be returned")

    loan_query_result.status = "returned"
    loan_query_result.returned_date = datetime.now()
    book_query_result.quantity += 1

    await db.commit()

    db_loan_return = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    ).filter(LoanModel.id == loan_id)
    )

    db_loan_result = db_loan_return.scalar_one_or_none()

    return db_loan_result


@router.patch("/{loan_id}", response_model=LoanResponse)
async def update_duedate(loan_id: int, loan_update: LoanUpdate, db: AsyncSession = Depends(get_db)):
    db_query = await db.execute(select(LoanModel).where(LoanModel.id == loan_id))
    query_result = db_query.scalar_one_or_none()

    if not query_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"loan with id {loan_id} does not exit")

    if loan_update.due_date is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Nothing to update")

    if query_result.status == "returned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"loan with {loan_id} already completed")

    query_result.due_date = loan_update.due_date

    await db.commit()
    db_loan_return = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    ).filter(LoanModel.id == loan_id)
    )
    db_loan_result = db_loan_return.scalar_one_or_none()
    return db_loan_result


@router.get("/", response_model=list[LoanResponse])
async def get_loans(db: AsyncSession = Depends(get_db)):
    db_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    )
    )

    query_result = db_query.scalars().all()
    return query_result


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    db_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.id == loan_id))

    query_result = db_query.scalar_one_or_none()

    if not query_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"loan id {loan_id} does not exist")

    return query_result
