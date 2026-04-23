from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel
from jose import JWTError, jwt


SECRET_KEY = "your-secret-key-change-in-production-please-use-random-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
SALT_LENGTH = 16


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)


app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
IMAGES_DIR = STATIC_DIR / "images"


IMAGES_DIR.mkdir(parents=True, exist_ok=True)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


class User(BaseModel):
    id: str
    username: str
    hashed_password: str
    created_at: str


class DiaryEntry(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    created_at: str
    updated_at: str
    images: List[str] = []


class ShareLink(BaseModel):
    id: str
    diary_id: str
    user_id: str
    password_hash: str
    share_token: str
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None


users: Dict[str, User] = {}
usernames: Dict[str, str] = {}
diaries: List[DiaryEntry] = []
share_links: Dict[str, ShareLink] = {}


def generate_salt() -> str:
    return secrets.token_hex(SALT_LENGTH)


def hash_password_with_salt(password: str, salt: str) -> str:
    salted_password = f"{salt}{password}"
    return hashlib.sha256(salted_password.encode('utf-8')).hexdigest()


def get_password_hash(password: str) -> str:
    salt = generate_salt()
    password_hash = hash_password_with_salt(password, salt)
    return f"{salt}${password_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split('$', 1)
    except ValueError:
        return False
    
    computed_hash = hash_password_with_salt(plain_password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token is None:
        return None
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None:
            return None
        token_data = TokenData(user_id=user_id, username=username)
    except JWTError:
        return None
    
    user = users.get(token_data.user_id)
    if user is None:
        return None
    return user


def hash_password_sha256(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_share_token() -> str:
    return str(uuid.uuid4())[:8] + str(uuid.uuid4())[:8]


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(context)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    current_user = await get_current_user_from_request(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    
    html_content = render_template(
        "login.html",
        {"request": request}
    )
    return HTMLResponse(content=html_content)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    current_user = await get_current_user_from_request(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    
    html_content = render_template(
        "register.html",
        {"request": request}
    )
    return HTMLResponse(content=html_content)


async def get_current_user_from_request(request: Request) -> Optional[User]:
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        return await get_current_user(token)
    
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
        return await get_current_user(token)
    
    return None


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    current_user = await get_current_user_from_request(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    user_diaries = [d for d in diaries if d.user_id == current_user.id]
    diaries_data = [d.model_dump() for d in user_diaries]
    
    html_content = render_template(
        "index.html",
        {"request": request, "diaries": diaries_data, "user": current_user}
    )
    return HTMLResponse(content=html_content)


@app.post("/api/register")
async def register(
    username: str = Form(...),
    password: str = Form(...)
):
    if username in usernames:
        return JSONResponse(
            status_code=400,
            content={"message": "用户名已存在"}
        )
    
    if len(username) < 3:
        return JSONResponse(
            status_code=400,
            content={"message": "用户名至少需要3个字符"}
        )
    
    if len(password) < 4:
        return JSONResponse(
            status_code=400,
            content={"message": "密码至少需要4个字符"}
        )
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user = User(
        id=user_id,
        username=username,
        hashed_password=hashed_password,
        created_at=now
    )
    
    users[user_id] = user
    usernames[username] = user_id
    
    return {
        "message": "注册成功",
        "user_id": user_id,
        "username": username
    }


@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_id = usernames.get(form_data.username)
    if not user_id or user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = users[user_id]
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    return response


@app.post("/api/logout")
async def logout():
    response = JSONResponse(content={"message": "已登出"})
    response.delete_cookie(key="access_token", path="/")
    return response


@app.get("/api/me")
async def get_me(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at
    }


@app.get("/api/diaries")
async def get_diaries(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    user_diaries = [d for d in diaries if d.user_id == current_user.id]
    return {"diaries": [d.model_dump() for d in user_diaries]}


@app.get("/api/diaries/{diary_id}")
async def get_diary(
    diary_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    for diary in diaries:
        if diary.id == diary_id and diary.user_id == current_user.id:
            return diary.model_dump()
    
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.post("/api/diaries")
async def create_diary(
    title: str = Form(...),
    content: str = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    diary_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    saved_images = []
    if images:
        for image in images:
            if image.filename:
                file_ext = Path(image.filename).suffix
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                file_path = IMAGES_DIR / unique_filename
                
                with open(file_path, "wb") as f:
                    content_bytes = await image.read()
                    f.write(content_bytes)
                
                saved_images.append(f"/static/images/{unique_filename}")
    
    diary = DiaryEntry(
        id=diary_id,
        user_id=current_user.id,
        title=title,
        content=content,
        created_at=now,
        updated_at=now,
        images=saved_images
    )
    diaries.insert(0, diary)
    
    return {"message": "日记创建成功", "diary": diary.model_dump()}


@app.put("/api/diaries/{diary_id}")
async def update_diary(
    diary_id: str,
    title: str = Form(...),
    content: str = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    for diary in diaries:
        if diary.id == diary_id and diary.user_id == current_user.id:
            diary.title = title
            diary.content = content
            diary.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if images:
                for image in images:
                    if image.filename:
                        file_ext = Path(image.filename).suffix
                        unique_filename = f"{uuid.uuid4()}{file_ext}"
                        file_path = IMAGES_DIR / unique_filename
                        
                        with open(file_path, "wb") as f:
                            content_bytes = await image.read()
                            f.write(content_bytes)
                        
                        diary.images.append(f"/static/images/{unique_filename}")
            
            return {"message": "日记更新成功", "diary": diary.model_dump()}
    
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.delete("/api/diaries/{diary_id}")
async def delete_diary(
    diary_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    for i, diary in enumerate(diaries):
        if diary.id == diary_id and diary.user_id == current_user.id:
            for image_path in diary.images:
                image_file = BASE_DIR / image_path.lstrip("/")
                if image_file.exists():
                    image_file.unlink()
            
            tokens_to_remove = [k for k, v in share_links.items() if v.diary_id == diary_id]
            for token in tokens_to_remove:
                del share_links[token]
            
            del diaries[i]
            return {"message": "日记删除成功"}
    
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.post("/api/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    if image.filename:
        file_ext = Path(image.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = IMAGES_DIR / unique_filename
        
        with open(file_path, "wb") as f:
            content_bytes = await image.read()
            f.write(content_bytes)
        
        return {
            "message": "图片上传成功",
            "url": f"/static/images/{unique_filename}"
        }
    
    return JSONResponse(status_code=400, content={"message": "无效的图片"})


@app.post("/api/diaries/{diary_id}/share")
async def share_diary(
    diary_id: str,
    password: str = Form(...),
    current_user: Optional[User] = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(
            status_code=401,
            content={"message": "未登录"}
        )
    
    for diary in diaries:
        if diary.id == diary_id and diary.user_id == current_user.id:
            share_token = generate_share_token()
            share_id = str(uuid.uuid4())
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            share_link = ShareLink(
                id=share_id,
                diary_id=diary_id,
                user_id=current_user.id,
                password_hash=hash_password_sha256(password),
                share_token=share_token,
                created_at=now,
                access_count=0
            )
            
            share_links[share_token] = share_link
            
            return {
                "message": "分享链接创建成功",
                "share_token": share_token,
                "share_url": f"/share/{share_token}"
            }
    
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.post("/api/share/{share_token}/verify")
async def verify_share_password(
    share_token: str,
    password: str = Form(...)
):
    if share_token not in share_links:
        return JSONResponse(status_code=404, content={"message": "分享链接不存在或已过期"})
    
    share_link = share_links[share_token]
    password_hash = hash_password_sha256(password)
    
    if password_hash != share_link.password_hash:
        return JSONResponse(status_code=401, content={"message": "密码错误"})
    
    for diary in diaries:
        if diary.id == share_link.diary_id:
            share_link.access_count += 1
            return {
                "message": "验证成功",
                "diary": diary.model_dump()
            }
    
    return JSONResponse(status_code=404, content={"message": "日记已被删除"})


@app.get("/share/{share_token}", response_class=HTMLResponse)
async def share_page(request: Request, share_token: str):
    if share_token not in share_links:
        html_content = render_template(
            "share_error.html",
            {
                "request": request,
                "error_message": "分享链接不存在或已过期"
            }
        )
        return HTMLResponse(content=html_content, status_code=404)
    
    share_link = share_links[share_token]
    
    html_content = render_template(
        "share.html",
        {
            "request": request,
            "share_token": share_token,
            "created_at": share_link.created_at,
            "access_count": share_link.access_count
        }
    )
    return HTMLResponse(content=html_content)
