import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.models.user import User
from app.models.book import Book
from app.security.security import hash_password


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        # Prevent asyncpg connections from being reused
        # across different event loops during tests.
        poolclass=NullPool)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@pytest_asyncio.fixture
async def override_get_db(test_session_factory):
    async def _override_get_db():
        async with test_session_factory() as session:
            yield session

    return _override_get_db


@pytest_asyncio.fixture
async def async_client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
async def test_admin(init_test_db, test_session_factory):
    async with test_session_factory() as db:
        admin = User(
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password_hash=hash_password("admin-password"),
            is_admin=True,
        )

        db.add(admin)

        await db.commit()
        await db.refresh(admin)

        yield admin


@pytest_asyncio.fixture
async def sample_book(init_test_db, test_session_factory):
    async with test_session_factory() as db:
        book = Book(
            title="Clean Code",
            author="Robert C. Martin",
            isbn="9880132350088",
            publisher="Prentice Hall",
            publisher_year=2008,
            summary="A handbook of agile software craftmanship",
            quantity=3
        )

        db.add(book)
        await db.commit()
        yield book
