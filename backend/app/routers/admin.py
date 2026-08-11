from fastapi import APIRouter

from app.auth.dependencies import RequireAdmin
from app.schemas import IskoristivostProvjeriResponse
from app.services.iskoristivost_alerts import provjeri_iskoristivost_alert

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/iskoristivost/provjeri", response_model=IskoristivostProvjeriResponse)
async def provjeri_iskoristivost_endpoint(_admin: RequireAdmin):
    """Ručno okidanje provjere iskorištenosti (općine >= prag) i slanja admin emaila."""
    return provjeri_iskoristivost_alert()
