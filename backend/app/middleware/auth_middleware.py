from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.security import decode_access_token
from app.database import SessionLocal
from app.models import Radnik

# Javne rute (bez Bearer tokena)
_JAVNE_PUTANJE = frozenset(
    {
        "/health",
        "/prijava",
        "/kupac/registracija",
        "/kupac/prijava",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)

# Kupac smije samo /kupac/* (osim javnih iznad)
_KUPAC_ZABRANJENI_PREFIKSI = (
    "/admin",
    "/radnici",
    "/dodijeli",
    "/dodjela",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Postavlja radnika u request.state; kupac dobiva 403 na interne rute."""

    async def dispatch(self, request: Request, call_next):
        request.state.radnik = None
        path = request.url.path
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                payload = decode_access_token(token)
                radnik_id = int(payload.get("sub", 0))
                db = SessionLocal()
                try:
                    radnik = db.get(Radnik, radnik_id)
                    if radnik and (not hasattr(radnik, "aktivan") or radnik.aktivan):
                        request.state.radnik = radnik
                        if radnik.uloga == "kupac":
                            blokiraj = any(
                                path.startswith(p) for p in _KUPAC_ZABRANJENI_PREFIKSI
                            )
                            if blokiraj:
                                return JSONResponse(
                                    status_code=403,
                                    content={
                                        "detail": "Kupci nemaju pristup ovoj ruti. Koristite portal."
                                    },
                                )
                            if not path.startswith("/kupac") and path not in _JAVNE_PUTANJE:
                                return JSONResponse(
                                    status_code=403,
                                    content={
                                        "detail": "Kupci imaju pristup samo portalu (/kupac/*)."
                                    },
                                )
                finally:
                    db.close()
            except Exception:
                pass
        return await call_next(request)
