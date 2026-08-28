from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.schemas.user import UserRegistration, UserResponse
from app.models.user import User as UserModel
from app.security.security import verify_password, hash_password, create_access_token, authenticate_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registration", response_model=UserResponse)
async def registration(new_user: UserRegistration, db: AsyncSession = Depends(get_db)):
    existing_email_query = await db.execute(
        select(UserModel)
        .where(UserModel.email == new_user.email))
    existing_email = existing_email_query.scalar_one_or_none()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User with email '{new_user.email}' already exists")

    query = await db.execute(select(func.count(UserModel.id)))
    user_count = query.scalar_one_or_none()

    is_admin = True if user_count == 0 else False
    #is_admin = (user_count == 0) shorter form

    register_user = UserModel(
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        email=new_user.email,
        password_hash=hash_password(new_user.password),
        is_admin=is_admin
)
    
    db.add(register_user)
    await db.commit()

    return register_user


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


