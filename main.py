from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routes import router as api_router

app = FastAPI()
app.include_router(api_router, prefix="/api")

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    templates_dir = BASE_DIR / "templates"
    index_path = templates_dir / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


@app.get("/health")
async def health():
    return {"status": "ok"}
