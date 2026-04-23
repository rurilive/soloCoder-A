import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_active_user, get_current_user
from app.models import MediaFile, MediaType, QualityLevel, User
from app.schemas import MediaFileResponse, UploadResponse
from app.utils.image_processor import get_image_info, process_image
from app.utils.security import generate_file_id, hash_filename

router = APIRouter(tags=["media"])
settings = get_settings()
templates = Jinja2Templates(directory="templates")


def get_file_url(request: Request, file_id: str, quality: str) -> str:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return f"{base_url}/file/{file_id}/{quality}"


async def save_upload_file(upload_file: UploadFile, save_path: Path) -> Path:
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return save_path


def is_allowed_type(mime_type: str) -> tuple[bool, Optional[MediaType]]:
    if mime_type in settings.ALLOWED_IMAGE_TYPES:
        return True, MediaType.IMAGE
    if mime_type in settings.ALLOWED_VIDEO_TYPES:
        return True, MediaType.VIDEO
    return False, None


@router.get("/upload", include_in_schema=False)
async def upload_page(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"user": current_user},
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected",
        )

    mime_type = file.content_type or "application/octet-stream"
    is_allowed, media_type = is_allowed_type(mime_type)

    if not is_allowed or media_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {mime_type} not allowed",
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes",
        )

    file_id = generate_file_id()
    base_filename = hash_filename(file.filename)
    original_ext = Path(file.filename).suffix.lower()

    date_dir = Path().joinpath(*current_user.uuid.split("-")[:2])
    upload_dir = settings.UPLOAD_DIR / date_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_path = upload_dir / f"{base_filename}_temp{original_ext}"
    await save_upload_file(file, temp_path)

    width: Optional[int] = None
    height: Optional[int] = None

    media_file = MediaFile(
        file_id=file_id,
        user_id=current_user.id,
        original_filename=file.filename,
        media_type=media_type,
        mime_type=mime_type,
        file_size=file_size,
        width=None,
        height=None,
        original_path="",
        original_size=file_size,
    )

    if media_type == MediaType.IMAGE:
        try:
            width, height, _ = get_image_info(temp_path)
            media_file.width = width
            media_file.height = height

            processed = await process_image(temp_path, base_filename, upload_dir)

            for quality, (path, size) in processed.items():
                relative_path = str(path.relative_to(settings.UPLOAD_DIR))
                if quality == "original":
                    media_file.original_path = relative_path
                    media_file.original_size = size
                elif quality == "standard":
                    media_file.standard_path = relative_path
                    media_file.standard_size = size
                elif quality == "low":
                    media_file.low_path = relative_path
                    media_file.low_size = size
                elif quality == "icon":
                    media_file.icon_path = relative_path
                    media_file.icon_size = size

        except Exception as e:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process image: {str(e)}",
            )
        finally:
            temp_path.unlink(missing_ok=True)
    else:
        final_path = upload_dir / f"{base_filename}_original{original_ext}"
        temp_path.rename(final_path)
        relative_path = str(final_path.relative_to(settings.UPLOAD_DIR))
        media_file.original_path = relative_path

    db.add(media_file)
    await db.commit()
    await db.refresh(media_file)

    response = MediaFileResponse(
        id=media_file.id,
        file_id=media_file.file_id,
        original_filename=media_file.original_filename,
        media_type=media_file.media_type.value,
        mime_type=media_file.mime_type,
        file_size=media_file.file_size,
        width=media_file.width,
        height=media_file.height,
        view_count=media_file.view_count,
        created_at=media_file.created_at,
        original_url=get_file_url(request, media_file.file_id, "original"),
        standard_url=get_file_url(request, media_file.file_id, "standard") if media_file.standard_path else None,
        low_url=get_file_url(request, media_file.file_id, "low") if media_file.low_path else None,
        icon_url=get_file_url(request, media_file.file_id, "icon") if media_file.icon_path else None,
    )

    return UploadResponse(success=True, message="File uploaded successfully", file=response)


@router.get("/file/{file_id}/{quality}")
async def serve_file(
    file_id: str,
    quality: str,
    db: AsyncSession = Depends(get_db),
):
    if quality not in ["original", "standard", "low", "icon"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quality level",
        )

    result = await db.execute(
        select(MediaFile).where(MediaFile.file_id == file_id)
    )
    media_file = result.scalar_one_or_none()

    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if not media_file.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File is not public",
        )

    path_attr = f"{quality}_path"
    file_path = getattr(media_file, path_attr)

    if not file_path:
        if quality == "original":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        file_path = media_file.original_path

    full_path = settings.UPLOAD_DIR / file_path

    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    await db.execute(
        update(MediaFile)
        .where(MediaFile.id == media_file.id)
        .values(view_count=MediaFile.view_count + 1)
    )
    await db.commit()

    return FileResponse(
        path=str(full_path),
        media_type=media_file.mime_type,
        filename=media_file.original_filename,
    )


@router.get("/dashboard", include_in_schema=False)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(MediaFile)
        .where(MediaFile.user_id == current_user.id)
        .order_by(MediaFile.created_at.desc())
        .limit(50)
    )
    files = result.scalars().all()

    file_responses = []
    for f in files:
        file_responses.append({
            "file_id": f.file_id,
            "original_filename": f.original_filename,
            "media_type": f.media_type.value,
            "file_size": f.file_size,
            "view_count": f.view_count,
            "created_at": f.created_at,
            "original_url": get_file_url(request, f.file_id, "original"),
            "standard_url": get_file_url(request, f.file_id, "standard") if f.standard_path else None,
            "low_url": get_file_url(request, f.file_id, "low") if f.low_path else None,
            "icon_url": get_file_url(request, f.file_id, "icon") if f.icon_path else None,
        })

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "files": file_responses,
            "user": current_user,
        },
    )
