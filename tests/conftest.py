import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import datetime, timezone, timedelta

from app.database.database import get_db
from app.database.base import Base
from app.main import app
from app.models.user import User
from app.models.book import Book
from app.models.loan import Loan
from app.security.security import hash_password


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def init_test_db(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
def test_session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False
    )


@pytest_asyncio.fixture
async def override_get_db(test_session_factory):
    async def _override_get_db():
        async with test_session_factory() as db:
            yield db

    return _override_get_db


@pytest.fixture
def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest_asyncio.fixture
async def test_user(init_test_db, test_session_factory):
    async with test_session_factory() as db:
        user = User(
            first_name="Test",
            last_name="User",
            email="user@test.com",
            password_hash=hash_password("test-password"),
            is_admin=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        yield user


@pytest_asyncio.fixture
async def test_book(init_test_db, test_session_factory):
    async with test_session_factory() as db:
        book = Book(
            isbn="Test-123",
            title="Test-Book",
            author="Test-Authour",
            publisher="Test-Publisher",
            publisher_year=2006,
            summary="Test-Summary"
        )

        db.add(book)
        await db.commit()
        await db.refresh(book)

        yield book


@pytest_asyncio.fixture
async def test_loan(init_test_db, test_session_factory, test_user, test_book):
    async with test_session_factory() as db:
        loan = Loan(
            user_id=test_user.id,
            book_id=test_book.id,
            due_date=datetime.now(timezone.utc) + timedelta(days=7)
        )

        db.add(loan)
        await db.commit()
        await db.refresh(loan)

        yield loan
