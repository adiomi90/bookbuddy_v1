from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.book import Book, BookResponse, UpdateBook, UpdateInventory
from app.models.book import Book as BookModel
from app.models.user import User as UserModel
from app.security.security import get_current_admin

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=BookResponse)
async def create_book(book: Book, db: AsyncSession = Depends(get_db),
                      current_admin: UserModel = Depends(get_current_admin)):
    existing_book = await db.execute(select(BookModel).where(BookModel.isbn == book.isbn))
    result = existing_book.scalar_one_or_none()

    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with title {book.title} and {book.isbn} already exists"
        )

    db_book = BookModel(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        publisher=book.publisher,
        publisher_year=book.publisher_year,
        summary=book.summary
    )

    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book


@router.get("/", response_model=list[BookResponse])
async def get_all_books(db: AsyncSession = Depends(get_db)):
    db_books = await db.execute(select(BookModel))
    results = db_books.scalars().all()

    return results


@router.get("/{book_id}", response_model=BookResponse)
async def get_book_by_id(book_id: int, db: AsyncSession = Depends(get_db),
                         current_admin: UserModel = Depends(get_current_admin)):
    db_book = await db.execute(select(BookModel).where(BookModel.id == book_id))
    result = db_book.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book with id {book_id} not found")
    return result


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, update_book: UpdateBook, db: AsyncSession = Depends(get_db),
                      current_admin: UserModel = Depends(get_current_admin)):
    db_book = await db.execute(select(BookModel).where(BookModel.id == book_id))
    result = db_book.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book with id {book_id} not found")

    if update_book.isbn is not None:
        existing_isbn = await db.execute(select(BookModel).where(
            BookModel.isbn == update_book.isbn,
            BookModel.id != book_id
        )
        )
        result_existing_isbn = existing_isbn.scalar_one_or_none()

        if result_existing_isbn:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another book with ISBN {update_book.isbn} already exists"
            )
    update_data = update_book.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(result, field, value)

    await db.commit()
    await db.refresh(result)

    return result


@router.patch("/{book_id}/inventory", response_model=BookResponse)
async def update_quantity(book_id: int, update_inventory: UpdateInventory,
                          db: AsyncSession = Depends(get_db),
                          current_admin: UserModel = Depends(get_current_admin)):
    db_query = await db.execute(select(BookModel).where(BookModel.id == book_id))
    result_query = db_query.scalar_one_or_none()

    if not result_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book id {book_id} does not exist")

    new_quantity = result_query.quantity + update_inventory.change
    if new_quantity < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"quantity can not be less than 0 - {new_quantity}")

    result_query.quantity = new_quantity
    await db.commit()
    await db.refresh(result_query)
    return result_query
