from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import (
    create_user_session,
    delete_user_session,
    get_current_active_user,
    get_current_user,
)
from app.models import User
from app.schemas import Token, UserCreate, UserResponse
from app.utils.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(tags=["auth"])
settings = get_settings()
templates = Jinja2Templates(directory="templates")


@router.get("/register", include_in_schema=False)
async def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": current_user},
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    if len(username) < 3 or len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 50 characters",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    existing_user = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/login", include_in_schema=False)
async def login_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": current_user},
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session_id, expires_at = await create_user_session(
        db, user.id, ip_address, user_agent
    )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        expires=int((expires_at - timedelta(seconds=0)).timestamp()),
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        expires=int((expires_at - timedelta(seconds=0)).timestamp()),
    )

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session_id = request.cookies.get("session_id")
    if session_id:
        await delete_user_session(db, session_id)

    response.delete_cookie("session_id")
    response.delete_cookie("access_token")

    return {"message": "Successfully logged out"}


@router.get("/logout", include_in_schema=False)
async def logout_page(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user:
        session_id = request.cookies.get("session_id")
        if session_id:
            await delete_user_session(db, session_id)

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_id")
    response.delete_cookie("access_token")
    return response


@router.get("/api/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user
