import datetime

from pydantic import BaseModel, Field, EmailStr, constr
from typing import List, Optional, Literal, Generic


class LoginTypeSchema(BaseModel):
    identifier_type: Literal["uid", "email"] = "uid"  # or use an enum for more control

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    uid: str


class RegistrationSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserSchema(BaseModel):
    uid: int
    username: str
    verified: bool
    email: EmailStr
    disabled: bool = False
    password: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class UidAuthSchema(BaseModel):
    uid: constr(strict=True, strip_whitespace=True)  # or your custom validation
    password: constr(strict=True, strip_whitespace=True)


class EmailAuthSchema(BaseModel):
    email: EmailStr
    password: constr(strict=True, strip_whitespace=True)
