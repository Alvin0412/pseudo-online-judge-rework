import pathlib
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Literal

import aiosmtplib
import logging
import sqlalchemy.exc
from fastapi import Depends, APIRouter, HTTPException, status, Path, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

import database
import utils.auth as auth
from models.user import User
from utils.settings import SERVER_PORT, SERVER_IP_ADDRESS, \
    SMTP_HOST_PORT, SMTP_HOST_NAME, SMTP_HOST_USER, SMTP_HOST_USER_PASSWORD
from .schema import TokenSchema, RegistrationSchema
from utils.logger import logger

router = APIRouter(
    prefix='/auth'
)


async def send_verify_email(user: auth.UserSchema):
    auth_code = auth.unique_auth_code(user.email, user.created_at, str(user.uid))
    verification_link = f'http://{SERVER_IP_ADDRESS}:{SERVER_PORT}/auth/register/{auth_code}?uid={user.uid}'

    message = MIMEMultipart("alternative")
    message['Subject'] = Header('[Project 1024] Verify Your Account', 'utf-8')
    message['From'] = Header(SMTP_HOST_USER, 'utf-8')
    message['To'] = Header(user.email, 'utf-8')

    text = f"Your verification link: {verification_link}"
    html = f"""\
    <html>
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            color: #333333;
          }}
          .content {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
          }}
          a {{
            color: #1a73e8;
            text-decoration: none;
          }}
          a:hover {{
            text-decoration: underline;
          }}
        </style>
      </head>
      <body>
        <div class="content">
          <h1>Verify Your Account</h1>
          <p>Hello, {user.username}<br>
             Please click on the link below to verify your account:</p>
          <p><a href="{verification_link}">Verify Your Account</a></p>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text, 'plain', 'utf-8')
    part2 = MIMEText(html, 'html', 'utf-8')

    message.attach(part1)
    message.attach(part2)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST_NAME,
            port=SMTP_HOST_PORT,
            username=SMTP_HOST_USER,
            password=SMTP_HOST_USER_PASSWORD,
            use_tls=True,
        )
    except aiosmtplib.SMTPException as e:
        # TODO: log error
        logger.error(f"Encountered error when sending verification email to {user.email}: {e.message}")
    logger.info(f"Verification email sent to {user.email}")


@router.post("/register/resend_verification")
async def resend_verification(
        email: Annotated[str, Query()],
        session: Annotated[database.Session, Depends(database.make_session)],
        background: BackgroundTasks
):
    try:
        print(email)
        user = session.query(User).filter(User.email == email).one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.verified:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="User is already verified")
        now = datetime.utcnow()
        if (now - user.updated_at) < timedelta(seconds=30):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Please wait before resending the email")

        user.updated_at = now
        session.add(user)
        session.commit()
        logger.info(f"Successfully updated user({user.uid}) and saved to database.")
    except sqlalchemy.exc.SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to resend verification email during database operation: {e.args}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error during database operation")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to resend verification email due to unexpected reason: {e.args}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error during database operation")
    background.add_task(send_verify_email, auth.UserSchema.model_validate(user))
    return {"message": "Verification email resent!"}


@router.get("/register/{auth_code}", response_model=TokenSchema)
async def verify_user(
        auth_code: Annotated[str, Path],
        uid: Annotated[int, Query(...)],
        session: Annotated[database.Session, Depends(database.make_session)],
):
    try:
        found_user: User = session.query(User).get(uid)
        now = datetime.utcnow()
        if found_user.verified:
            raise ValueError("User already verified!")
        if (now - found_user.created_at) > timedelta(minutes=10):
            raise ValueError("Verification link expired.")
        actual_code = auth.unique_auth_code(found_user.email, found_user.created_at, str(found_user.uid))
        if actual_code != auth_code:
            raise ValueError("Invalid authentication code.")

        found_user.verified = True
        session.add(found_user)
        session.commit()
    except ValueError as e:
        session.rollback()
        logger.error(f"Invalid credentials during verification with user({uid}): {e.args}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        logger.error(f"Failed to verify user({uid}) during database operation: {e.args}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed!")
    access_token = auth.create_access_token(data={"sub": str(found_user.uid)})
    logger.info(f"User({uid}) successfully logged in with access bearer token of {access_token}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
        registration_data: RegistrationSchema,
        session: Annotated[database.Session, Depends(database.make_session)],
        background: BackgroundTasks
):
    is_exist = session.query(User).where(User.email == registration_data.email).one_or_none()
    if is_exist is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    try:
        new_user = User(
            username=registration_data.username,
            email=registration_data.email,
            disabled=False,
            verified=False,
            password=auth.make_hashed_password(registration_data.password)
        )
        session.add(new_user)
        session.flush()
        session.refresh(new_user)
        new_user_schema = auth.UserSchema.model_validate(new_user)
        background.add_task(send_verify_email, new_user_schema)
        session.commit()
        logger.info(f"Successfully created an unverified user account: {new_user_schema.model_dump()}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to register user with registration_data of {registration_data.model_dump()} due to {e.args}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {e.args}")
    return {"message": "Please check your email to verify your account!"}


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[database.Session, Depends(database.make_session)],
        login_type: Literal["uid", "email"] = "email"
):
    username = form_data.username
    password = form_data.password

    # Determine if identifier is an email or uid based on additional body parameter
    if login_type == "email":
        user = await auth.authenticate_user_by_email(session, username, password)
    elif login_type == "uid":
        user = await auth.authenticate_user(session, username, password)
    else:
        logger.error(f"Invalid identifier type provided({login_type}) with form_data({form_data.__dict__})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid identifier type provided",
        )
    if user is None:
        logger.error(f"Incorrect username or password with form_data({form_data.__dict__})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": str(user.uid)})
    logger.info(f"Successfully login with bearer access token of {access_token} from {user.uid}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/token/user_details")
async def login_for_access_token(
        user: Annotated[auth.UserSchema, Depends(auth.require_login)],
):
    logger.info(f"Successfully returned details from {user.uid}")
    return auth.UserSchema.model_validate(user)
