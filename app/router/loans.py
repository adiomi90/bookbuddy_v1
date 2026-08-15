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
from datetime import datetime, timezone


router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=LoanResponse)
async def create_loan(loan: Loan, db: AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(UserModel).where(UserModel.id == loan.user_id))
    user = user_query.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {loan.user_id} does not exist"
        )
    book_query = await db.execute(select(BookModel).where(BookModel.id == loan.book_id))
    book = book_query.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {loan.book_id} does not exist"
        )
    if book.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient book in stock for book id {loan.book_id}"
        )

    existing_loan_query = await db.execute(
        select(LoanModel)
        .where(
            LoanModel.user_id == loan.user_id,
            LoanModel.book_id == loan.book_id,
            LoanModel.status == "borrowed"
            )
        )
    
    existing_loan = existing_loan_query.scalar_one_or_none()

    if existing_loan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {loan.user_id} already has active loan for  {loan.book_id}"
        )

    book.quantity -= 1

    new_loan = LoanModel(
        user_id=loan.user_id,
        book_id=loan.book_id,
        due_date=loan.due_date
    )

    db.add(new_loan)
    await db.commit()

    loan_query = await db.execute(
        select(LoanModel)
        .options(
            selectinload(LoanModel.user),
            selectinload(LoanModel.book)
        )
        .where(LoanModel.id == new_loan.id)
    )
    new_loan = loan_query.scalar_one()
    return new_loan


@router.patch("/{loan_id}/return", response_model=LoanResponse)
async def return_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    loan_query = await db.execute(
                        select(LoanModel)
                        .options(
                            selectinload(LoanModel.user),
                            selectinload(LoanModel.book)    
                                 )
                        .where(LoanModel.id == loan_id))
    
    loan = loan_query.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Loan with id {loan_id} was not found")

    if loan.status == "returned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Loan id {loan_id} already returned")

    book = loan.book
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book id {loan.book_id} can't be returned")

    loan.status = "returned"
    loan.returned_date = datetime.now(timezone.utc)
    book.quantity += 1

    await db.commit()

    await db.refresh(loan)
    await db.refresh(book)
    return loan


@router.patch("/{loan_id}", response_model=LoanResponse)
async def update_duedate(loan_id: int, loan_update: LoanUpdate, db: AsyncSession = Depends(get_db)):
    loan_query = await db.execute(
        select(LoanModel)
        .options(
            selectinload(LoanModel.user),
            selectinload(LoanModel.book)
        )
        .where(LoanModel.id == loan_id))
    
    loan = loan_query.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"loan with id {loan_id} does not exist")

    if loan_update.due_date is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Nothing to update")

    if loan.status == "returned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"loan with {loan_id} already completed")

    loan.due_date = loan_update.due_date

    await db.commit()

    loan_query = await db.execute(
    select(LoanModel)
    .options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    )
    .where(LoanModel.id == loan_id)
)

    loan = loan_query.scalar_one()

    return loan


@router.get("/", response_model=list[LoanResponse])
async def get_loans(db: AsyncSession = Depends(get_db)):
    loans_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book))
    )

    loans = loans_query.scalars().all()
    return loans


@router.get("/overdue", response_model=list[LoanResponse])
async def get_overdue_loans(db: AsyncSession = Depends(get_db)):
    overdue_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.status == "overdue"))

    overdue_loans = overdue_query.scalars().all()
    return overdue_loans


@router.get("/user/{user_id}", response_model=list[LoanResponse])
async def get_loans_for_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = user_query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User id {user_id} does not exist")

    user_loan_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    ).filter(LoanModel.user_id == user_id))

    user_loans = user_loan_query.scalars().all()

    return user_loans


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    loan_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.id == loan_id))

    loan = loan_query.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"loan id {loan_id} does not exist")

    return loan
