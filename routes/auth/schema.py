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

