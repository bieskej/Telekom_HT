import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.auth_middleware import AuthMiddleware
from app.routers.auth import router as auth_router
from app.routers.msisdn import router as msisdn_router
from app.routers.kvalitete import router as kvalitete_router
from app.routers.opcine import router as opcine_router
from app.routers.radnici import router as radnici_router
from app.routers.izvoz import router as izvoz_router
from app.routers.admin import router as admin_router
from app.routers.admin_email import router as admin_email_router
from app.routers.admin_audit import router as admin_audit_router
from app.routers.admin_statistika import router as admin_statistika_router
from app.routers.email_test import router as email_test_router
from app.routers.catalog import router as catalog_router
from app.routers.hijerarhija import router as hijerarhija_router
from app.routers.kupac import router as kupac_router
from app.routers.portabilnost import router as portabilnost_router
from app.routers.servisni_nalog import router as servisni_nalog_router
from app.scheduler import shutdown_scheduler, start_scheduler
from app.services.pdf_fonts import init_pdf_fonts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    font_info = init_pdf_fonts()
    app.state.pdf_font_info = font_info
    logger.info(
        "PDF fontovi: %s registrirani iz %s (backend_root=%s, cwd=%s)",
        font_info.get("registered"),
        font_info.get("fonts_dir"),
        font_info.get("backend_root"),
        font_info.get("cwd"),
    )
    if not font_info.get("cwd_matches_backend", True):
        logger.warning(
            "Backend nije pokrenut iz backend/ mape – koristite scripts/start-backend.ps1"
        )
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="HT Eronet API",
    description="API za automatsku dodjelu telefonskih brojeva",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    from app.services.pdf_fonts import pdf_font_health

    font = pdf_font_health()
    ok = font.get("pdf_font") == "dejavu" and font.get("status") == "ok"
    return {
        "status": "ok" if ok else "degraded",
        "pdf_font": font.get("pdf_font", "error"),
        "fonts_dir": font.get("fonts_dir"),
        "backend_root": font.get("backend_root"),
        "cwd": font.get("cwd"),
        "cwd_matches_backend": font.get("cwd_matches_backend"),
        "pdf_font_detail": font.get("detail"),
    }


app.include_router(auth_router)
app.include_router(msisdn_router)
app.include_router(radnici_router)
app.include_router(opcine_router)
app.include_router(kvalitete_router)
app.include_router(izvoz_router)
app.include_router(admin_router)
app.include_router(admin_email_router)
app.include_router(admin_audit_router)
app.include_router(admin_statistika_router)
app.include_router(email_test_router)
app.include_router(catalog_router)
app.include_router(hijerarhija_router)
app.include_router(kupac_router)
app.include_router(portabilnost_router)
app.include_router(servisni_nalog_router)
