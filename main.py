from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.database import init_db
from app.router.users import router as user_router
from app.router.books import router as book_router
from app.router.loans import router as loan_router
from app.scheduled_task.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    #schedular to check for due_date
    scheduler.start()
    await init_db()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(book_router)
app.include_router(loan_router)
