from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models import Radnik

security_scheme = HTTPBearer(auto_error=False)

Uloga = str


async def get_current_radnik(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
) -> Radnik:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niste prijavljeni.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        radnik_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravan ili istekao token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    radnik = db.get(Radnik, radnik_id)
    if not radnik:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Radnik nije pronađen.")
    if hasattr(radnik, "aktivan") and radnik.aktivan is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Račun nije aktivan.")
    return radnik


def require_uloge(*dozvoljene: Uloga):
    async def _checker(radnik: Radnik = Depends(get_current_radnik)) -> Radnik:
        if radnik.uloga not in dozvoljene:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nemate ovlasti za ovu radnju.",
            )
        return radnik

    return _checker


RequireProdajaIliAdmin = Annotated[Radnik, Depends(require_uloge("prodaja", "admin"))]
RequirePregled = Annotated[Radnik, Depends(require_uloge("promet", "admin", "prodaja"))]
RequireAdmin = Annotated[Radnik, Depends(require_uloge("admin"))]
RequireKupac = Annotated[Radnik, Depends(require_uloge("kupac"))]
