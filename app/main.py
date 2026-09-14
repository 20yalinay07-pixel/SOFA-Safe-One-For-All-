"""
SOFA (Safe One For All) - Ana Uygulama Giriş Noktası
FastAPI tabanlı, tamamen yerel-öncelikli (local-first) çok modüllü asistan.

Çalıştırmak için:
    uvicorn app.main:app --reload
veya
    python -m app.main
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.modules.chat.router import router as chat_router
from app.modules.media.router import router as media_router
from app.modules.music.router import router as music_router
from app.modules.privacy.router import router as privacy_router

BASE_DIR = Path(__file__).resolve().parent.parent

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Tamamen yerel çalışan, gizlilik odaklı çok işlevli AI yardımcı uygulaması.",
    version="0.1.0",
)

# Statik dosyalar (CSS, JS, görseller)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Modül router'larını uygulamaya bağla
app.include_router(chat_router)
app.include_router(media_router)
app.include_router(music_router)
app.include_router(privacy_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Ana arayüzü (giriş animasyonu + uygulama kabuğu) döndürür."""
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})


@app.get("/api/health")
async def health_check() -> dict:
    """Basit sağlık kontrolü; hassas hiçbir bilgi döndürmez."""
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.sofa_host, port=settings.sofa_port, reload=True)
