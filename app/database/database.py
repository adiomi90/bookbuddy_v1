import os
from fastapi import FastAPI
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.users import Base
from contextlib import asynccontextmanager
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(bind=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)