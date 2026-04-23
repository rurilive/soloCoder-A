from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import async_session_maker, init_db
from app.dependencies import get_current_user as get_user
from app.models import User
from app.routers import auth, media

settings = get_settings()
templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("./data").mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="图床服务",
    description="高性能图片托管服务，支持多质量转换和分享链接",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    user = None
    try:
        async with async_session_maker() as session:
            user = await get_user(request, session)
    except Exception:
        pass
    
    request.state.user = user
    request.scope["user"] = user

    response = await call_next(request)
    return response


@app.get("/")
async def home(request: Request):
    user: Optional[User] = getattr(request.state, "user", None)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user},
    )


app.include_router(auth.router)
app.include_router(media.router)
