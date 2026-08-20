from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.loan import Loan, LoanResponse, LoanUpdate, LoanDuration
from app.models.loan import Loan as LoanModel
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from app.security.security import get_current_user, get_current_admin
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.get("/me", response_model=list[LoanResponse])
async def get_loans(db: AsyncSession = Depends(get_db),
                    current_user: UserModel = Depends(get_current_user)):
    query = select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    )

    if not current_user.is_admin:
        query = query.where(LoanModel.user_id == current_user.id)

    query = await db.execute(query)
    loans = query.scalars().all()

    return loans


@router.get("/overdue", response_model=list[LoanResponse])
async def get_overdue_loans(db: AsyncSession = Depends(get_db),
                            current_user: UserModel = Depends(get_current_user)):
    query = select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.status == "overdue")

    if not current_user.is_admin:
        query = query.where(LoanModel.user_id == current_user.id)

    query = await db.execute(query)
    overdue_loans = query.scalars().all()

    return overdue_loans


@router.get("/user/{user_id}", response_model=list[LoanResponse])
async def get_loans_for_user(user_id: int, db: AsyncSession = Depends(get_db),
                             current_admin: UserModel = Depends(get_current_admin)):

    query = select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)).where(
            LoanModel.user_id == user_id
    )

    query = await db.execute(query)
    loans = query.scalars().all()

    return loans


@router.get("/{loan_id}", response_model=LoanResponse,)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db),
                   current_admin: UserModel = Depends(get_current_admin)):
    loan_query = await db.execute(select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.id == loan_id))

    loan = loan_query.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"loan id {loan_id} does not exist")

    return loan


@router.post("/{user_id}", response_model=LoanResponse)
async def create_loan(user_id: int, loan: Loan, db: AsyncSession = Depends(get_db),
                      current_user: UserModel = Depends(get_current_admin)):
    user_query = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = user_query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User {user_id} does not exist")

    book_query = await db.execute(
        select(BookModel)
        .where(BookModel.id == loan.book_id))

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
            LoanModel.user_id == user_id,
            LoanModel.book_id == loan.book_id,
            LoanModel.status == "borrowed"
        )
    )

    existing_loan = existing_loan_query.scalar_one_or_none()

    if existing_loan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {user_id} already has active loan for book {loan.book_id}"
        )

    book.quantity -= 1

    duedate = datetime.now(timezone.utc) + timedelta(days=loan.duration)

    five_or_more_active_loans_query = await db.execute(
        select(LoanModel)
        .where(LoanModel.user_id == user_id,
               or_(
                   LoanModel.status == "borrowed",
                   LoanModel.status == "overdue"
               )
               )
    )

    five_or_more_active_loans = five_or_more_active_loans_query.scalars().all()
    if len(five_or_more_active_loans) >= 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User {user_id} already has 5 loans")

    new_loan = LoanModel(
        user_id=user_id,
        book_id=loan.book_id,
        due_date=duedate
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
async def return_loan(loan_id: int, db: AsyncSession = Depends(get_db),
                      current_admin: UserModel = Depends(get_current_admin)):
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
async def update_duedate(loan_id: int, loan_update: LoanUpdate, db: AsyncSession = Depends(get_db),
                         current_admin: UserModel = Depends(get_current_admin)):
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
