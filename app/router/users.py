from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.user import User, UserResponse, UpdateUser
from app.models.user import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/db-test")
async def get_test(db: AsyncSession = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=UserResponse)
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(UserModel).where(UserModel.email == user.email))
    result = existing_user.scalar_one_or_none()

    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {user.email} already exists"
        )

    db_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserResponse])
async def get_user(db: AsyncSession = Depends(get_db)):
    db_users = await db.execute(select(UserModel))
    results = db_users.scalars().all()

    return results


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {user_id} not found")
    return result


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UpdateUser, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {user_id} not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(result, field, value)

    await db.commit()
    await db.refresh(result)

    return result


@router.delete("/{user_id}")
async def delete_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {user_id} not found")
    await db.delete(result)
    await db.commit()

    return {"message": f"User with id: {user_id} deleted successfully"}
