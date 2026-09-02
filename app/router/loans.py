from fastapi import APIRouter, HTTPException, status
from fastapi import Depends

from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.loan import Loan, LoanResponse, LoanUpdate, RenewalDuration, PaginationResponse, UserFineResponse, VerifyPayment
from app.models.loan import Loan as LoanModel
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from app.security.security import get_current_user, get_current_admin
from app.utils.loan_helper import loan_with_fine, calculate_loan_fine


from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.get("/me", response_model=PaginationResponse[LoanResponse])
async def get_loans(skip: int = 0,
                    limit: int = 20,
                    db: AsyncSession = Depends(get_db),
                    current_user: UserModel = Depends(get_current_user)):
    query = select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)
    )

    if not current_user.is_admin:
        query = query.where(LoanModel.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    pagination_query = query.offset(skip).limit(limit)
    result = await db.execute(pagination_query)
    loans = result.scalars().all()

    return PaginationResponse(
        items=loans,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/me/fines", response_model=UserFineResponse)
async def get_user_fines(db: AsyncSession = Depends(get_db),
                         current_user: UserModel = Depends(get_current_user)):
    query = select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).where(
        LoanModel.user_id == current_user.id,
        LoanModel.status == "overdue"
    )

    loans_query = await db.execute(query)
    overdue_loans = loans_query.scalars().all()

    loan_with_fines = [loan_with_fine(loan) for loan in overdue_loans]

    total_fines = sum(loan["fine_amount"] for loan in loan_with_fines)

    return UserFineResponse(
        total_fines=total_fines,
        overdue_loans=loan_with_fines
    )


@router.get("/overdue", response_model=PaginationResponse[LoanResponse])
async def get_overdue_loans(skip: int = 0,
                            limit: int = 20,
                            db: AsyncSession = Depends(get_db),
                            current_user: UserModel = Depends(get_current_user)):
    query = select(LoanModel).options(
        selectinload(LoanModel.book),
        selectinload(LoanModel.user)
    ).filter(LoanModel.status == "overdue")

    if not current_user.is_admin:
        query = query.where(LoanModel.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    pagination_query = query.offset(skip).limit(limit)
    result = await db.execute(pagination_query)
    overdue_loans = result.scalars().all()

    loans_with_fine = [loan_with_fine(loan) for loan in overdue_loans]
    return PaginationResponse(
        items=loans_with_fine,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/user/{user_id}", response_model=PaginationResponse[LoanResponse])
async def get_loans_for_user(user_id: int,
                             skip: int = 0,
                             limit: int = 20,
                             db: AsyncSession = Depends(get_db),
                             current_admin: UserModel = Depends(get_current_admin)):

    query = select(LoanModel).options(
        selectinload(LoanModel.user),
        selectinload(LoanModel.book)).where(
            LoanModel.user_id == user_id
    )

    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    pagination_query = query.offset(skip).limit(limit)
    result = await db.execute(pagination_query)
    loans = result.scalars().all()

    return PaginationResponse(
        items=loans,
        total=total,
        skip=skip,
        limit=limit
    )


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


@router.post("/pay-all-fine", response_model=dict)
async def pay_all_fine(db: AsyncSession = Depends(get_db),
                       current_user: UserModel = Depends(get_current_user)
                       ):
    unpaid_loans_query = await db.execute(
        select(LoanModel)
        .options(selectinload(LoanModel.book))
        .where(
            LoanModel.user_id == current_user.id,
            LoanModel.payment_status == "unpaid"
        )
    )

    unpaid_loans = unpaid_loans_query.scalars().all()

    if not unpaid_loans:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No unpaid fines found")

    total_amount = sum(loan.fine_amount for loan in unpaid_loans)

    now = datetime.now(timezone.utc)
    for loan in unpaid_loans:
        loan.payment_status = "pending"
        loan.payment_submitted_date = now

    await db.commit()

    return {
        "message": f"Successfully submitted payment for {len(unpaid_loans)} loan(s)",
        "total_amount": total_amount,
        "loans_updated": [loan.book.title for loan in unpaid_loans]
    }


@router.post("/{user_id}", response_model=LoanResponse)
async def create_loan(user_id: int, loan: Loan, db: AsyncSession = Depends(get_db),
                      current_user: UserModel = Depends(get_current_admin)):
    user_query = await db.execute(
        select(UserModel)
        .where(UserModel.id == user_id))
    user = user_query.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User {user_id} does not exist")

    book_query = await db.execute(
        select(BookModel)
        .where(BookModel.id == loan.book_id)
        .with_for_update()
    )

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

    book.quantity -= 1
    duedate = datetime.now(timezone.utc) + timedelta(days=loan.duration)
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


@router.patch("/renew", response_model=LoanResponse)
async def renew_loan(title: str,
                     duration: RenewalDuration,
                     db: AsyncSession = Depends(get_db),
                     current_user: UserModel = Depends(get_current_user)):

    query = select(LoanModel).join(BookModel).where(
        BookModel.title.ilike(f"%{title}%"),
        LoanModel.user_id == current_user.id,
        LoanModel.status == "borrowed"
    )

    query = await db.execute(query)
    loan_query = query.scalars().all()

    if not loan_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No active loan found for the match")

    if len(loan_query) > 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="multiple book match please be specific")

    loan = loan_query[0]

    if loan.due_date < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="book already overdue, can't be renewed")

    if loan.renewal_count >= 2:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Maximum renewals reached")

    loan.due_date = loan.due_date + timedelta(days=duration.renewal_duration)

    loan.renewal_count += 1

    await db.commit()
    await db.refresh(loan)

    loan_query = await db.execute(
        select(LoanModel).options(
            selectinload(LoanModel.user),
            selectinload(LoanModel.book)
        ).where(LoanModel.id == loan.id))

    loan = loan_query.scalar_one()

    return loan


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

    _, final_fine = calculate_loan_fine(loan)
    loan.fine_amount = final_fine

    if loan.fine_amount > 0:
        loan.payment_status = "unpaid"

    loan.status = "returned"
    loan.returned_date = datetime.now(timezone.utc)
    book.quantity += 1

    await db.commit()

    await db.refresh(loan)
    await db.refresh(book)
    return loan_with_fine(loan)

@router.patch("/{loan_id}/verify-payment", response_model=LoanResponse)
async def verify_payment(loan_id: int,
                          request: VerifyPayment,
                            db: AsyncSession = Depends(get_db),
                            admin: UserModel = Depends(get_current_admin)
                            ):
    loan_query = await db.execute(select(LoanModel)
                                  .options(selectinload(LoanModel.book),
                                           selectinload(LoanModel.user))
                                  .where(LoanModel.id == loan_id))


    loan = loan_query.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Loan doesn't exist")

    if loan.payment_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Payment is not pending verification"
        ) 

    if request.action == "approve":
        loan.payment_status = "paid"
    else:
        loan.payment_status = "rejected"

    await db.commit()
    await db.refresh(loan)

    return loan_with_fine(loan)






    
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
