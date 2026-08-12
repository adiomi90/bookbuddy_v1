from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class User(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)