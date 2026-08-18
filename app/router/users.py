from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.user import User, UserResponse, UserUpdate, AdminUserCreate
from app.models.user import User as UserModel
from app.security.security import get_current_user, get_current_admin, hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/db-test")
async def get_test(current_user: UserModel = Depends(get_current_user)):
    return {"message": "authenticated"}


@router.post("/", response_model=UserResponse)
async def create_user(user: AdminUserCreate, current_admin: UserModel = Depends(get_current_admin),
                      db: AsyncSession = Depends(get_db)):
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
        email=user.email,
        password_hash=hash_password(user.password)
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
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
    result = db_user.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {user_id} not found")

    if user_update.email is not None:
        existing_email = await db.execute(select(UserModel)
                                          .where(UserModel.email == user_update.email,
                                                 UserModel.id != user_id))
        result_existing_email = existing_email.scalar_one_or_none()

        if result_existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Another user with {user_update.email} already exists")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(result, field, value)

    await db.commit()
    await db.refresh(result)

    return result


