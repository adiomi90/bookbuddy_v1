from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.database import init_db
from app.router.users import router as user_router
from app.router.books import router as book_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(book_router)
