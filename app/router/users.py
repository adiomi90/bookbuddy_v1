from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.user import User, UserResponse, UpdateUser
from app.models.users import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/db-test", response_model=UserResponse)
def get_test(db: Session = Depends(get_db)):
    return {"database": "connected"}


@router.post("/", response_model=UserResponse)
def create_user(user: User, db: Session = Depends(get_db)):
    db_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserResponse])
def get_user(db: Session = Depends(get_db)):
    return db.query(UserModel).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.id == user_id).first()


@router.delete("/{user_id}")
def delete_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    db.delete(user)
    db.commit()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int,user_update: UpdateUser, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    return db_user
    
