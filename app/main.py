from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.database import init_db
from app.router.users import router as user_router
from app.router.books import router as book_router
from app.router.loans import router as loan_router
from app.scheduled_task.scheduler import scheduler
from app.router.auth import router as auth_router
from app.router.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # schedular to check for due_date
    scheduler.start()
    await init_db()
    yield
    scheduler.shutdown()

app = FastAPI(
    title="BookBuddy Library Management System",
    description="A production-ready REST API for managing users, books, and library loans.",
    lifespan=lifespan
)


@app.get("/")
def welcome():
    return {
        "message": "Welcome to the BookBuddy Libarary Management System",
        "docs": "/docs",
        "status": "healthy"
    }


app.include_router(user_router)
app.include_router(book_router)
app.include_router(loan_router)
app.include_router(auth_router)
app.include_router(analytics_router)
