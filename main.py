from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel


app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
IMAGES_DIR = STATIC_DIR / "images"


IMAGES_DIR.mkdir(parents=True, exist_ok=True)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


class DiaryEntry(BaseModel):
    id: str
    title: str
    content: str
    created_at: str
    updated_at: str
    images: List[str] = []


class ShareLink(BaseModel):
    id: str
    diary_id: str
    password_hash: str
    share_token: str
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0


diaries: List[DiaryEntry] = []
share_links: Dict[str, ShareLink] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_share_token() -> str:
    return str(uuid.uuid4())[:8] + str(uuid.uuid4())[:8]


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(context)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    diaries_data = [d.model_dump() for d in diaries]
    html_content = render_template(
        "index.html",
        {"request": request, "diaries": diaries_data}
    )
    return HTMLResponse(content=html_content)


@app.get("/api/diaries")
async def get_diaries():
    return {"diaries": [d.model_dump() for d in diaries]}


@app.get("/api/diaries/{diary_id}")
async def get_diary(diary_id: str):
    for diary in diaries:
        if diary.id == diary_id:
            return diary.model_dump()
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.post("/api/diaries")
async def create_diary(
    title: str = Form(...),
    content: str = Form(...),
    images: Optional[List[UploadFile]] = File(None)
):
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
    images: Optional[List[UploadFile]] = File(None)
):
    for diary in diaries:
        if diary.id == diary_id:
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
async def delete_diary(diary_id: str):
    for i, diary in enumerate(diaries):
        if diary.id == diary_id:
            for image_path in diary.images:
                image_file = BASE_DIR / image_path.lstrip("/")
                if image_file.exists():
                    image_file.unlink()
            
            del diaries[i]
            return {"message": "日记删除成功"}
    
    return JSONResponse(status_code=404, content={"message": "日记不存在"})


@app.post("/api/upload-image")
async def upload_image(image: UploadFile = File(...)):
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
    password: str = Form(...)
):
    for diary in diaries:
        if diary.id == diary_id:
            share_token = generate_share_token()
            share_id = str(uuid.uuid4())
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            share_link = ShareLink(
                id=share_id,
                diary_id=diary_id,
                password_hash=hash_password(password),
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
    password_hash = hash_password(password)
    
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
