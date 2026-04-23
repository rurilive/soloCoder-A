from datetime import datetime, timedelta
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Session as DbSession, User
from app.utils.security import decode_access_token, generate_session_id

settings = get_settings()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
) -> Optional[User]:
    session_id = request.cookies.get("session_id")

    if session_id:
        result = await db.execute(
            select(DbSession).where(
                DbSession.session_id == session_id,
                DbSession.expires_at > datetime.utcnow(),
            )
        )
        db_session = result.scalar_one_or_none()

        if db_session:
            user_result = await db.execute(select(User).where(User.id == db_session.user_id))
            user = user_result.scalar_one_or_none()
            if user and user.is_active:
                return user

    if access_token:
        payload = decode_access_token(access_token)
        if payload:
            username: str = payload.get("sub")
            if username:
                result = await db.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    return user

    return None


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def create_user_session(
    db: AsyncSession,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, datetime]:
    session_id = generate_session_id()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    db_session = DbSession(
        session_id=session_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    return session_id, expires_at


async def delete_user_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(select(DbSession).where(DbSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
        return True
    return False
