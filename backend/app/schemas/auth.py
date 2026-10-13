from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: Role = Role.RESEARCHER


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: Role

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
