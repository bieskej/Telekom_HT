from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from app.auth.dependencies import RequireAdmin
from app.services.email_service import send_email_with_attachment, smtp_configured
from app.services.invoice_email import generiraj_pdf_racun

router = APIRouter(tags=["email"])


class TestEmailRequest(BaseModel):
    to_email: EmailStr


class TestEmailResponse(BaseModel):
    poslano: bool
    poruka: str
    smtp_konfiguriran: bool


@router.post("/test-email", response_model=TestEmailResponse)
async def test_email_endpoint(
    payload: TestEmailRequest,
    _admin: RequireAdmin,
):
    pdf = generiraj_pdf_racun(
        "Test",
        "Korisnik",
        "0101000500012",
        str(payload.to_email),
        "+387 61 000 000",
        "silver",
        10.0,
    )
    if not smtp_configured():
        return TestEmailResponse(
            poslano=False,
            poruka=(
                "SMTP nije potpun. U backend/.env postavite SMTP_HOST, SMTP_USER i "
                "SMTP_PASSWORD (Gmail App Password, 16 znakova)."
            ),
            smtp_konfiguriran=False,
        )
    ok, err = send_email_with_attachment(
        str(payload.to_email),
        "Test email - HT Eronet",
        "Ovo je testna poruka za provjeru SMTP konfiguracije HT Eronet.\n\nU privitku je testni PDF racun (test_racun.pdf).",
        pdf,
        "test_racun.pdf",
    )
    return TestEmailResponse(
        poslano=ok,
        poruka=err or "Email je uspješno poslan.",
        smtp_konfiguriran=True,
    )
