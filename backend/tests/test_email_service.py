from unittest.mock import MagicMock, patch

from app.services.email_service import (
    notifikacija_status_poslije_slanja,
    send_email_with_attachment,
    smtp_configured,
)


def test_smtp_configured_false():
    with patch("app.services.email_service.settings") as s:
        s.smtp_host = ""
        assert smtp_configured() is False


def test_smtp_configured_true():
    with patch("app.services.email_service.settings") as s:
        s.smtp_host = "smtp.example.com"
        assert smtp_configured() is True


def test_send_email_without_smtp():
    with patch("app.services.email_service.settings") as s:
        s.smtp_host = ""
        ok, err = send_email_with_attachment("a@b.ba", "Subj", "Body", b"%PDF", "t.pdf")
    assert ok is False
    assert "SMTP" in (err or "")


def test_send_email_success():
    mock_server = MagicMock()
    with (
        patch("app.services.email_service.settings") as s,
        patch("app.services.email_service.smtplib.SMTP", return_value=mock_server),
    ):
        s.smtp_host = "localhost"
        s.smtp_port = 25
        s.smtp_user = ""
        s.smtp_password = ""
        s.smtp_from = "test@eronet.ba"
        s.smtp_use_tls = False
        ok, err = send_email_with_attachment("admin@eronet.ba", "Test", "Poruka", None)
    assert ok is True
    assert err is None


def test_notifikacija_status_nedostaje_smtp():
    with patch("app.services.email_service.smtp_configured", return_value=False):
        assert notifikacija_status_poslije_slanja(False) == "nedostaje_smtp"
