from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.book import Book, BookResponse, UpdateBook
from app.models.book import Book as BookModel

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=BookResponse)
async def create_book(book: Book, db: AsyncSession = Depends(get_db)):
    existing_book = await db.execute(select(BookModel).where(BookModel.isbn == book.isbn))
    result = existing_book.scalar_one_or_none()

    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with title {book.title} and {book.isbn} already exits"
        )

    db_book = BookModel(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        publisher=book.publisher,
        publisher_year=book.publisher_year,
        summary=book.summary,
        quantity=book.quantity

    )

    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book


@router.get("/", response_model=list[BookResponse])
async def get_user(db: AsyncSession = Depends(get_db)):
    db_users = await db.execute(select(BookModel))
    results = db_users.scalars().all()

    return results


@router.get("/{user_id}", response_model=BookResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(BookModel).where(BookModel.id == user_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {user_id} not found")
    return result


@router.patch("/{user_id}", response_model=BookResponse)
async def update_user(book_id: int, user_update: UpdateBook, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(BookModel).where(BookModel.id == book_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book with id {book_id} not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(result, field, value)

    await db.commit()
    await db.refresh(result)

    return result


@router.delete("/{user_id}")
async def delete_user_by_id(book_id: int, db: AsyncSession = Depends(get_db)):
    db_book = await db.execute(select(BookModel).where(BookModel.id == book_id))
    result = db_book.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {book_id} not found")
    await db.delete(result)
    await db.commit()

    return {"message": f"User with id: {book_id} deleted successfully"}
