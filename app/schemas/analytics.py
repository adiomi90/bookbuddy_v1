from pydantic import BaseModel
from typing import List, Optional


class TopBorrowedBook(BaseModel):
    book_title: str
    borrow_count: int

class TopBorrowedBookResponse(BaseModel):
    books: List[TopBorrowedBook]