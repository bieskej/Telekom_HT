"""Smoke testovi za seed_opcine_geo.py – sve općine s brojevima imaju lat/lon."""

from sqlalchemy import text

from scripts.seed_opcine_geo import KOORDINATE, popuni_koordinate


def test_sve_opcine_s_brojevima_imaju_koordinate(db):
    rez = popuni_koordinate()
    assert rez["azurirano"] >= 1
    nedostaje = db.execute(
        text(
            """
            SELECT DISTINCT o.naziv
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE o.lat IS NULL OR o.lon IS NULL
            """
        )
    ).fetchall()
    assert nedostaje == [], (
        f"Općine s brojevima bez koordinata: {[r.naziv for r in nedostaje]}"
    )


def test_koordinate_unutar_geografije_bih(db):
    """BiH je otprilike u rasponu lat 42.5-45.3, lon 15.7-19.7."""
    for naziv, (lat, lon) in KOORDINATE.items():
        assert 42.0 <= lat <= 46.0, f"{naziv}: lat {lat} izvan BiH"
        assert 15.0 <= lon <= 20.0, f"{naziv}: lon {lon} izvan BiH"


def test_idempotentnost_skripte(db):
    """Dva uzastopna pokretanja moraju dati isto stanje (UPDATE, ne INSERT)."""
    prije = db.execute(text("SELECT COUNT(*) FROM opcine")).scalar()
    popuni_koordinate()
    popuni_koordinate()
    poslije = db.execute(text("SELECT COUNT(*) FROM opcine")).scalar()
    assert prije == poslije, "Skripta je dodala redove (treba samo UPDATE)"


def test_kljucne_opcine_u_rjecniku():
    for op in ("Mostar", "Stolac", "Čapljina", "Neum", "Sarajevo", "Banja Luka", "Brčko"):
        assert op in KOORDINATE, f"Općina {op} mora biti u KOORDINATE rječniku"
