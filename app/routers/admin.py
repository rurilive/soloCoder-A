from datetime import datetime
from typing import Optional
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import User, MediaFile, MediaType
from app.routers.media import get_file_url

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()


@router.get("/admin", include_in_schema=False)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    user_count_result = await db.execute(select(func.count(User.id)))
    user_count = user_count_result.scalar()

    file_count_result = await db.execute(select(func.count(MediaFile.id)))
    file_count = file_count_result.scalar()

    deleted_count_result = await db.execute(
        select(func.count(MediaFile.id)).where(MediaFile.is_deleted == True)
    )
    deleted_count = deleted_count_result.scalar()

    expired_count_result = await db.execute(
        select(func.count(MediaFile.id)).where(MediaFile.is_expired == True)
    )
    expired_count = expired_count_result.scalar()

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(100)
    )
    users = users_result.scalars().all()

    user_stats = []
    for user in users:
        user_files_result = await db.execute(
            select(func.count(MediaFile.id)).where(MediaFile.user_id == user.id)
        )
        user_file_count = user_files_result.scalar()

        user_stats.append({
            "id": user.id,
            "uuid": user.uuid,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "file_count": user_file_count,
        })

    files_result = await db.execute(
        select(MediaFile)
        .order_by(MediaFile.created_at.desc())
        .limit(200)
    )
    files = files_result.scalars().all()

    file_responses = []
    for f in files:
        if not f.is_expired and f.expires_at:
            if datetime.utcnow() > f.expires_at:
                f.is_expired = True

    await db.commit()

    for f in files:
        file_responses.append({
            "id": f.id,
            "file_id": f.file_id,
            "original_filename": f.original_filename,
            "media_type": f.media_type.value,
            "file_size": f.file_size,
            "view_count": f.view_count,
            "created_at": f.created_at,
            "expires_at": f.expires_at,
            "is_expired": f.is_expired,
            "is_deleted": f.is_deleted,
            "deleted_at": f.deleted_at,
            "deleted_reason": f.deleted_reason,
            "require_token": f.require_token,
            "allowed_referers": f.allowed_referers,
            "user_id": f.user_id,
            "original_url": get_file_url(request, f.file_id, "original"),
            "standard_url": get_file_url(request, f.file_id, "standard") if f.standard_path else None,
            "low_url": get_file_url(request, f.file_id, "low") if f.low_path else None,
            "icon_url": get_file_url(request, f.file_id, "icon") if f.icon_path else None,
        })

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": current_user,
            "user_count": user_count,
            "file_count": file_count,
            "deleted_count": deleted_count,
            "expired_count": expired_count,
            "users": user_stats,
            "files": file_responses,
        },
    )


@router.get("/admin/users/{user_id}/files", include_in_schema=False)
async def admin_user_files(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    target_user_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_user_result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    files_result = await db.execute(
        select(MediaFile)
        .where(MediaFile.user_id == user_id)
        .order_by(MediaFile.created_at.desc())
    )
    files = files_result.scalars().all()

    for f in files:
        if not f.is_expired and f.expires_at:
            if datetime.utcnow() > f.expires_at:
                f.is_expired = True

    await db.commit()

    file_responses = []
    for f in files:
        file_responses.append({
            "id": f.id,
            "file_id": f.file_id,
            "original_filename": f.original_filename,
            "media_type": f.media_type.value,
            "file_size": f.file_size,
            "view_count": f.view_count,
            "created_at": f.created_at,
            "expires_at": f.expires_at,
            "is_expired": f.is_expired,
            "is_deleted": f.is_deleted,
            "deleted_at": f.deleted_at,
            "deleted_reason": f.deleted_reason,
            "require_token": f.require_token,
            "allowed_referers": f.allowed_referers,
            "user_id": f.user_id,
            "original_url": get_file_url(request, f.file_id, "original"),
        })

    return templates.TemplateResponse(
        request=request,
        name="admin_user_files.html",
        context={
            "user": current_user,
            "target_user": {
                "id": target_user.id,
                "username": target_user.username,
                "email": target_user.email,
            },
            "files": file_responses,
        },
    )


@router.post("/api/admin/users/{user_id}/toggle-active")
async def admin_toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot toggle your own account",
        )

    target_user.is_active = not target_user.is_active
    await db.commit()

    return {
        "success": True,
        "is_active": target_user.is_active,
    }


@router.post("/api/admin/users/{user_id}/toggle-admin")
async def admin_toggle_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot toggle your own admin status",
        )

    target_user.is_admin = not target_user.is_admin
    await db.commit()

    return {
        "success": True,
        "is_admin": target_user.is_admin,
    }


@router.post("/api/admin/media/{file_id}/hard-delete")
async def admin_hard_delete_file(
    file_id: str,
    reason: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(MediaFile).where(MediaFile.file_id == file_id))
    media_file = result.scalar_one_or_none()

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    files_to_delete = []
    if media_file.original_path:
        files_to_delete.append(media_file.original_path)
    if media_file.standard_path:
        files_to_delete.append(media_file.standard_path)
    if media_file.low_path:
        files_to_delete.append(media_file.low_path)
    if media_file.icon_path:
        files_to_delete.append(media_file.icon_path)

    deleted_files = []
    for file_path in files_to_delete:
        if file_path:
            full_path = settings.UPLOAD_DIR / file_path
            if full_path.exists():
                try:
                    full_path.unlink()
                    deleted_files.append(str(full_path))
                except Exception as e:
                    print(f"Failed to delete file {full_path}: {e}")

    user_folder = settings.UPLOAD_DIR / Path(media_file.original_path).parts[0]
    if user_folder.exists():
        try:
            has_files = any(user_folder.iterdir())
            if not has_files:
                shutil.rmtree(user_folder)
        except Exception as e:
            print(f"Failed to clean up folder {user_folder}: {e}")

    await db.execute(delete(MediaFile).where(MediaFile.file_id == file_id))
    await db.commit()

    return {
        "success": True,
        "message": f"File permanently deleted. {len(deleted_files)} physical files removed.",
        "deleted_files": deleted_files,
    }


@router.post("/api/admin/media/{file_id}/restore")
async def admin_restore_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(MediaFile).where(MediaFile.file_id == file_id))
    media_file = result.scalar_one_or_none()

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if not media_file.is_deleted:
        return {
            "success": True,
            "message": "File is not deleted",
        }

    media_file.is_deleted = False
    media_file.deleted_at = None
    media_file.deleted_reason = None

    await db.commit()

    return {
        "success": True,
        "message": "File has been restored by admin",
    }


@router.get("/admin/cleanup", include_in_schema=False)
async def admin_cleanup_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    expired_count_result = await db.execute(
        select(func.count(MediaFile.id)).where(
            MediaFile.is_expired == True,
            MediaFile.is_deleted == False,
        )
    )
    expired_count = expired_count_result.scalar()

    soft_deleted_count_result = await db.execute(
        select(func.count(MediaFile.id)).where(MediaFile.is_deleted == True)
    )
    soft_deleted_count = soft_deleted_count_result.scalar()

    return templates.TemplateResponse(
        request=request,
        name="admin_cleanup.html",
        context={
            "user": current_user,
            "expired_count": expired_count,
            "soft_deleted_count": soft_deleted_count,
        },
    )


@router.post("/api/admin/cleanup/expired")
async def admin_cleanup_expired(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=30)

    expired_result = await db.execute(
        select(MediaFile).where(
            MediaFile.is_expired == True,
            MediaFile.is_deleted == False,
        )
    )
    expired_files = expired_result.scalars().all()

    for f in expired_files:
        f.is_deleted = True
        f.deleted_at = datetime.utcnow()
        f.deleted_reason = "Auto cleanup: expired file"

    await db.commit()

    return {
        "success": True,
        "message": f"Soft deleted {len(expired_files)} expired files",
        "count": len(expired_files),
    }


@router.post("/api/admin/cleanup/permanent")
async def admin_cleanup_permanent(
    days: int = Form(90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from datetime import datetime, timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    deleted_result = await db.execute(
        select(MediaFile).where(
            MediaFile.is_deleted == True,
            MediaFile.deleted_at <= cutoff_date,
        )
    )
    deleted_files = deleted_result.scalars().all()

    deleted_count = 0
    for f in deleted_files:
        files_to_delete = []
        if f.original_path:
            files_to_delete.append(f.original_path)
        if f.standard_path:
            files_to_delete.append(f.standard_path)
        if f.low_path:
            files_to_delete.append(f.low_path)
        if f.icon_path:
            files_to_delete.append(f.icon_path)

        for file_path in files_to_delete:
            if file_path:
                full_path = settings.UPLOAD_DIR / file_path
                if full_path.exists():
                    try:
                        full_path.unlink()
                    except Exception:
                        pass

        await db.execute(delete(MediaFile).where(MediaFile.id == f.id))
        deleted_count += 1

    await db.commit()

    return {
        "success": True,
        "message": f"Permanently deleted {deleted_count} files",
        "count": deleted_count,
    }
