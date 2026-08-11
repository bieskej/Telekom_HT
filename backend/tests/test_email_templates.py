from app.services.email_templates import render_email_template


def test_dodjela_template_renderira_se_bez_greske():
    html = render_email_template(
        "dodjela.html",
        {
            "ime": "Ana",
            "prezime": "Anić",
            "broj_formatiran": "036 303 040",
            "datum": "19.05.2026.",
            "kvaliteta": "Gold",
            "adresa": "Ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert "Ana" in html
    assert "Anić" in html
    assert "036 303 040" in html
    assert "Pohranite ovu poruku kao potvrdu" in html


def test_karantena_start_sadrzi_datum():
    html = render_email_template(
        "karantena_start.html",
        {
            "ime": "Marko",
            "prezime": "Marković",
            "broj_formatiran": "036 200 100",
            "datum_isteka": "18.07.2026.",
            "karantena_dana": 60,
        },
    )
    assert "18.07.2026." in html
    assert "karanten" in html.lower()


def test_digest_admin_top_5_opcina():
    html = render_email_template(
        "digest_admin.html",
        {
            "razdoblje": "12.05.2026. – 19.05.2026.",
            "ukupno_dodjela": 42,
            "top_opcine": [
                {"naziv": "Mostar", "broj": 10},
                {"naziv": "Stolac", "broj": 8},
                {"naziv": "Čapljina", "broj": 6},
                {"naziv": "Jablanica", "broj": 4},
                {"naziv": "Konjic", "broj": 2},
            ],
            "top_radnici": [{"ime": "Admin Admin", "broj": 5}],
            "po_danima": [{"datum": "19.05.2026.", "broj": 3}],
        },
    )
    assert "Mostar" in html
    assert "Stolac" in html
    assert "Top 5 općina" in html
