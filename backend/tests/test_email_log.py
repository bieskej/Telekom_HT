from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import text


def test_send_kreira_log_red_status_poslano(db):
    from app.services.email_service import send_html_email

    mock_server = MagicMock()
    with patch("app.services.email_service.smtp_configured", return_value=True), patch(
        "app.services.email_service.smtplib.SMTP"
    ) as smtp_cls:
        smtp_cls.return_value.__enter__.return_value = mock_server
        ok, err, log_id = send_html_email(
            "test@example.com",
            "Test predmet",
            "karantena_end.html",
            {"ime": "A", "prezime": "B", "broj_formatiran": "036 100 200"},
            db=db,
        )
    assert ok is True
    assert err is None
    assert log_id is not None
    row = db.execute(
        text("SELECT status, primatelj FROM email_log WHERE id = :id"),
        {"id": log_id},
    ).fetchone()
    assert row.status == "poslano"
    assert row.primatelj == "test@example.com"


def test_send_greska_kreira_log_red_status_greska(db):
    from app.services.email_service import send_html_email

    with patch("app.services.email_service.smtp_configured", return_value=True), patch(
        "app.services.email_service.smtplib.SMTP"
    ) as smtp_cls:
        smtp_cls.return_value.__enter__.return_value.send_message.side_effect = OSError(
            "SMTP connection refused"
        )
        ok, err, log_id = send_html_email(
            "fail@example.com",
            "Greška test",
            "karantena_end.html",
            {"ime": "A", "prezime": "B", "broj_formatiran": "036 100 200"},
            db=db,
        )
    assert ok is False
    assert err
    assert log_id is not None
    row = db.execute(
        text("SELECT status, error_text FROM email_log WHERE id = :id"),
        {"id": log_id},
    ).fetchone()
    assert row.status == "greska"
    assert "refused" in (row.error_text or "").lower()


def test_resend_endpoint_kreira_novi_log(client: TestClient, db, admin_token: str):
    row = db.execute(
        text(
            """
            INSERT INTO email_log (primatelj, predmet, status, html_tijelo, sent_at)
            VALUES ('resend@test.hr', 'Ponovno slanje', 'poslano', '<p>Test HTML</p>', NOW())
            RETURNING id
            """
        )
    ).fetchone()
    db.commit()
    log_id = row.id

    with patch("app.services.email_notifications.send_html_email") as mock_send:
        mock_send.return_value = (True, None, 999)
        res = client.post(
            f"/admin/email-resend/{log_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["novi_log_id"] == 999
    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args
    assert args[0] == "resend@test.hr"
    assert kwargs.get("html_body") == "<p>Test HTML</p>"
