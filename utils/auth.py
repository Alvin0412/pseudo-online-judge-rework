import hashlib
from datetime import datetime, timedelta
from typing import Annotated

import pydantic.v1
import sqlalchemy.exc
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

import database
from models.user import User
from .common_schemas import TokenDataSchema, UserSchema, UidAuthSchema, EmailAuthSchema
from .settings import JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def unique_auth_code(email: str, timestamp: datetime, uid: str = ""):
    data_encode = f"{email}{timestamp.isoformat()}"
    hash_1st = hashlib.md5(data_encode.encode('utf-8')).hexdigest()
    hash_2nd = hashlib.sha256(f"{hash_1st}{uid}".encode('utf-8')).hexdigest()
    return hash_2nd


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def make_hashed_password(password: str):
    return pwd_context.hash(password)


def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None,
):
    encode_data = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # default
        print(datetime.utcnow())
    encode_data["exp"] = expire
    print(encode_data)
    encoded_jwt = jwt.encode(encode_data, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_user_from_uid(session: database.Session, uid: str) -> UserSchema | None:
    try:
        user: User = session.query(User).get(uid)
        if user is None:
            raise ValueError
    except (ValueError, sqlalchemy.exc.SQLAlchemyError):
        return None
    return UserSchema.model_validate(user)


async def get_user_from_email(session: database.Session, email: str) -> UserSchema | None:
    try:
        user = session.query(User).where(User.email == email).one_or_none()
        if user is None:
            raise ValueError
    except (ValueError, sqlalchemy.exc.IntegrityError):
        return None
    return UserSchema.model_validate(user)


async def authenticate_user(
        session: database.Session,
        uid: str,
        password: str
):
    try:
        pending = UidAuthSchema(uid=uid, password=password)
    except pydantic.ValidationError:
        return None
    user = await get_user_from_uid(session, uid)
    if user is None:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def authenticate_user_by_email(
        session: database.Session,
        email: str,
        password: str
):
    try:
        pending = EmailAuthSchema(email=email, password=password)
    except pydantic.ValidationError:
        return None
    user = await get_user_from_email(session, email)
    if user is None:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print(datetime.now())
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        uid: str = payload.get("sub")
        if uid is None:
            raise credentials_exception
        token_data = TokenDataSchema(uid=uid)
    except JWTError as e:
        print(e)
        raise credentials_exception
    user = await get_user_from_uid(session, token_data.uid)

    if user is None:
        raise credentials_exception
    return user


async def require_login(user: Annotated[UserSchema, Depends(get_current_user)]):
    if user.disabled or not user.verified:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
