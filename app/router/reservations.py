from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.database.database import get_db
from app.models.user import User as UserModel
from app.models.book import Book as BookModel
from app.models.reservation import Reservation as ReservationModel
from app.schemas.reservation import ReservationCreate, ReservationResponse, ReservationListResponse, ReservationCancelResponse, ReservationCancelRequest, ReservationApproveResponse
from app.security.security import get_current_user, get_current_admin
from datetime import datetime, timedelta, timezone
router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    conditions = []
    if reservation_data.isbn:
        conditions.append(BookModel.isbn == reservation_data.isbn)
    if reservation_data.title:
        conditions.append(BookModel.title.ilike(f"%{reservation_data.title}%"))

    if not conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either ISBN or title must be provided"
        )

    find_book = select(BookModel).where(or_(*conditions))
    result = await db.execute(find_book)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    check_exisiting_reservation = await db.execute(
        select(ReservationModel).where(
            ReservationModel.user_id == current_user.id,
            ReservationModel.book_id == book.id,
            ReservationModel.status.in_(["pending", "ready"])
        )
    )

    existing_reservation = check_exisiting_reservation.scalar_one_or_none()

    if existing_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have an active reservation for {book.title} "
        )

    new_reservation = ReservationModel(
        user_id=current_user.id,
        book_id=book.id,
        status="pending",
        expires_at=None
    )

    db.add(new_reservation)
    await db.commit()
    await db.refresh(new_reservation)

    return ReservationResponse(
        id=new_reservation.id,
        book_id=book.id,
        book_title=book.title,
        status=new_reservation.status,
        expires_at=new_reservation.expires_at,
        created_at=new_reservation.created_at,
        updated_at=new_reservation.updated_at
    )


@router.get("/", response_model=ReservationListResponse)
async def list_my_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    query = select(ReservationModel).options(
        selectinload(ReservationModel.book)
    ).where(
        ReservationModel.user_id == current_user.id
    )

    result = await db.execute(query)
    reservations = result.scalars().all()

    reservation_response = []
    for reservation in reservations:
        reservation_response.append(
            ReservationResponse(
                id=reservation.id,
                book_id=reservation.book_id,
                book_title=reservation.book.title,
                status=reservation.status,
                expires_at=reservation.expires_at,
                created_at=reservation.created_at,
                updated_at=reservation.updated_at
            )
        )

    return ReservationListResponse(reservations=reservation_response)


@router.patch("/cancel", response_model=ReservationCancelResponse)
async def user_cancel_reservation(
    cancel_data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    conditions = []
    if cancel_data.isbn:
        conditions.append(BookModel.isbn == cancel_data.isbn)
    if cancel_data.title:
        conditions.append(BookModel.title.ilike(f"%{cancel_data.title}%"))

    if not conditions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Either ISBN or Title must be provided")

    find_book = select(BookModel).where(or_(*conditions))
    result = await db.execute(find_book)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    check_existing_reservation = await db.execute(
        select(ReservationModel)
        .options(
            selectinload(ReservationModel.book),
            selectinload(ReservationModel.user))
        .where(
            ReservationModel.user_id == current_user.id,
            ReservationModel.book_id == book.id,
            ReservationModel.status.in_(["pending", "ready"])
        )
    )

    reservation = check_existing_reservation.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No reservation for this book")

    if reservation.status in ["cancelled", "picked_up", "expired"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel reservation with status {reservation.status}"
        )

    reservation.status = "cancelled"

    await db.commit()
    await db.refresh(reservation)

    return ReservationCancelResponse(
        id=reservation.id,
        book_title=reservation.book.title,
        user_email=reservation.user.email,
        status=reservation.status,
        cancelled_at=reservation.updated_at,
        note="User Cancelled"
    )


@router.patch("/{reservation_id}/cancel", response_model=ReservationCancelResponse)
async def admin_cancel_reservation(
    reservation_id: int,
    cancel_data: ReservationCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    query = select(ReservationModel).options(
        selectinload(ReservationModel.book),
        selectinload(ReservationModel.user)
    ).where(
        ReservationModel.id == reservation_id
    )
    result = await db.execute(query)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The reservation doesn't exist")

    if reservation.status in ["cancelled", "picked_up", "expired"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel reservation with status {reservation.status}"
        )

    reservation.status = "cancelled"
    reservation.cancellation_note = cancel_data.note

    await db.commit()
    await db.refresh(reservation)

    return ReservationCancelResponse(
        id=reservation.id,
        book_title=reservation.book.title,
        user_email=reservation.user.email,
        status=reservation.status,
        cancelled_at=reservation.updated_at,
        note=cancel_data.note
    )


@router.patch("/{reservation_id}/approve", response_model=ReservationApproveResponse)
async def admin_approve_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin)
):
    query = select(ReservationModel).options(
        selectinload(ReservationModel.book),
        selectinload(ReservationModel.user)
    ).where(
        ReservationModel.id == reservation_id
    )

    result = await db.execute(query)
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Reservation not found"
                            )

    if reservation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve reservation with status {reservation.status}"

        )

    reservation.status = "ready"
    reservation.expires_at = datetime.now(timezone.utc) + timedelta(days=3)

    await db.commit()
    await db.refresh(reservation)

    return ReservationApproveResponse(
        id=reservation.id,
        book_title=reservation.book.title,
        user_email=reservation.user.email,
        status=reservation.status,
        expires_at=reservation.expires_at,
        message="Reservatioin approved. User has 3 days to pick up the book"
    )
