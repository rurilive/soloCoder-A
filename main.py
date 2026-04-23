import re
import bcrypt
import jinja2
from markupsafe import Markup
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc
from itsdangerous import URLSafeTimedSerializer

from app.database import init_db, get_db
from app.models import Post, Category, Tag, User


TEMPLATE_DIR = Path(__file__).parent / "templates"
SECRET_KEY = "waterfall-blog-secret-key-2026-change-in-production"
SESSION_COOKIE_NAME = "blog_session"
SESSION_MAX_AGE = 24 * 60 * 60

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
    cache_size=0,
    auto_reload=True,
)

serializer = URLSafeTimedSerializer(SECRET_KEY)


def linebreaks_filter(text):
    if not text:
        return Markup('')
    text = str(text)
    paragraphs = text.split('\n\n')
    result = []
    for para in paragraphs:
        para = para.replace('\n', '<br>\n')
        result.append(f'<p>{para}</p>')
    return Markup('\n\n'.join(result))


env.filters['linebreaks'] = linebreaks_filter


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except:
        return False


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def verify_session_token(token: str) -> int | None:
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user_id")
    except:
        return None


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None
    
    user_id = verify_session_token(session_token)
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user


async def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = await get_current_user(request, db)
    if not user or user.is_admin != 1:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def url_for(request: Request, name: str, **path_params) -> str:
    return request.url_for(name, **path_params)


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(**context)


def create_default_admin(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    default_password = "admin123"
    
    if not admin:
        admin = User(
            username="admin",
            password_hash=get_password_hash(default_password),
            is_admin=1,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("默认管理员已创建: username=admin, password=admin123")
    else:
        if not verify_password(default_password, admin.password_hash):
            admin.password_hash = get_password_hash(default_password)
            db.commit()
            print("管理员密码已重置为: admin123")
    
    return admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()
    
    yield


app = FastAPI(title="瀑布流博客", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


def category_to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'posts_count': len(category.posts) if category.posts else 0
    }


def tag_to_dict(tag):
    return {
        'id': tag.id,
        'name': tag.name,
        'posts_count': len(tag.posts) if tag.posts else 0
    }


def get_categories_dict(db: Session):
    categories = db.query(Category).all()
    return [category_to_dict(c) for c in categories]


def get_tags_dict(db: Session):
    tags = db.query(Tag).all()
    return [tag_to_dict(t) for t in tags]


def get_or_create_tags(db: Session, tag_names: str) -> list:
    tags = []
    if not tag_names:
        return tags
    
    tag_list = [t.strip() for t in tag_names.split(',') if t.strip()]
    for tag_name in tag_list:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tags.append(tag)
    return tags


@app.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)
):
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": "管理员登录",
        "current_user": None,
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("login.html", context)
    return HTMLResponse(content=html)


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        categories_dict = get_categories_dict(db)
        tags_dict = get_tags_dict(db)
        
        context = {
            "request": request,
            "categories": categories_dict,
            "tags": tags_dict,
            "title": "管理员登录",
            "current_user": None,
            "error": "用户名或密码错误",
            "url_for": lambda name, **path_params: url_for(request, name, **path_params),
        }
        
        html = render_template("login.html", context)
        return HTMLResponse(content=html, status_code=401)
    
    session_token = create_session_token(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)
):
    posts = db.query(Post).filter(Post.is_published == 1).order_by(desc(Post.created_at)).all()
    
    post_dicts = [post.to_dict() for post in posts]
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "posts": post_dicts,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": "首页",
        "current_user": current_user.to_dict() if current_user else None,
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("index.html", context)
    return HTMLResponse(content=html)


@app.get("/post/{post_id}", response_class=HTMLResponse)
async def post_detail(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    post.view_count += 1
    db.commit()
    
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "post": post.to_dict(),
        "categories": categories_dict,
        "tags": tags_dict,
        "title": post.title,
        "current_user": current_user.to_dict() if current_user else None,
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("post.html", context)
    return HTMLResponse(content=html)


@app.get("/create", response_class=HTMLResponse)
async def create_post_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": "新建文章",
        "post": None,
        "current_user": current_user.to_dict(),
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("form.html", context)
    return HTMLResponse(content=html)


@app.post("/create")
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(default=""),
    cover_image: str = Form(default=""),
    category_name: str = Form(default=""),
    tag_names: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    slug = slugify(title)
    
    category = None
    if category_name:
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.commit()
            db.refresh(category)
    
    tags = get_or_create_tags(db, tag_names)
    
    post = Post(
        title=title,
        slug=slug,
        content=content,
        excerpt=excerpt or content[:100],
        cover_image=cover_image,
        category=category,
        tags=tags,
        is_published=1
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return RedirectResponse(url=f"/post/{post.id}", status_code=303)


@app.get("/edit/{post_id}", response_class=HTMLResponse)
async def edit_post_form(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    post_dict = post.to_dict()
    post_dict['tag_names'] = ', '.join([tag.name for tag in post.tags])
    
    context = {
        "request": request,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": "编辑文章",
        "post": post_dict,
        "current_user": current_user.to_dict(),
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("form.html", context)
    return HTMLResponse(content=html)


@app.post("/edit/{post_id}")
async def update_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(default=""),
    cover_image: str = Form(default=""),
    category_name: str = Form(default=""),
    tag_names: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    post.title = title
    post.slug = slugify(title)
    post.content = content
    post.excerpt = excerpt or content[:100]
    post.cover_image = cover_image
    
    if category_name:
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.commit()
            db.refresh(category)
        post.category = category
    else:
        post.category = None
    
    post.tags = get_or_create_tags(db, tag_names)
    
    db.commit()
    
    return RedirectResponse(url=f"/post/{post.id}", status_code=303)


@app.post("/delete/{post_id}")
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    db.delete(post)
    db.commit()
    
    return RedirectResponse(url="/", status_code=303)


@app.get("/category/{category_name}", response_class=HTMLResponse)
async def posts_by_category(
    request: Request,
    category_name: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.name == category_name).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    posts = db.query(Post).filter(
        Post.category_id == category.id,
        Post.is_published == 1
    ).order_by(desc(Post.created_at)).all()
    
    post_dicts = [post.to_dict() for post in posts]
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "posts": post_dicts,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": f"分类: {category_name}",
        "current_category": category_name,
        "current_user": current_user.to_dict() if current_user else None,
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("index.html", context)
    return HTMLResponse(content=html)


@app.get("/tag/{tag_name}", response_class=HTMLResponse)
async def posts_by_tag(
    request: Request,
    tag_name: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)
):
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    posts = db.query(Post).filter(
        Post.tags.any(id=tag.id),
        Post.is_published == 1
    ).order_by(desc(Post.created_at)).all()
    
    post_dicts = [post.to_dict() for post in posts]
    categories_dict = get_categories_dict(db)
    tags_dict = get_tags_dict(db)
    
    context = {
        "request": request,
        "posts": post_dicts,
        "categories": categories_dict,
        "tags": tags_dict,
        "title": f"标签: {tag_name}",
        "current_tag": tag_name,
        "current_user": current_user.to_dict() if current_user else None,
        "url_for": lambda name, **path_params: url_for(request, name, **path_params),
    }
    
    html = render_template("index.html", context)
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
