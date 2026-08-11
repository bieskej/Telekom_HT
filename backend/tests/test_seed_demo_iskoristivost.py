"""Testovi za seed_demo_iskoristivost (logika + opcionalna integracija)."""

import pytest
from sqlalchemy import text

from scripts.seed_demo_iskoristivost import (
    DEMO_CILJEVI,
    cilj_zauzeto,
    generiraj_demo_jmbg,
    sync_opcina,
)

# Offseti samo za integracijski test — ne preklapaju se s ručnim seedom (0 / 10_000).
TEST_JMBG_OFFSET_GORAZDE = 800_000
TEST_JMBG_OFFSET_CRNICI = 810_000

TEST_DEMO_CLEANUP = """
    UPDATE msisdn
    SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
        email = NULL, adresa = NULL, grad = NULL, postanski_broj = NULL,
        datum_dodjele = NULL, rezerviran_do = NULL
    WHERE ime = 'Demo'
      AND (prezime LIKE 'Korisnik800%' OR prezime LIKE 'Korisnik810%')
"""


def test_cilj_zauzeto_zaokruzuje():
    assert cilj_zauzeto(1000, 51.0) == 510
    assert cilj_zauzeto(1000, 91.0) == 910
    assert cilj_zauzeto(0, 51.0) == 0


def test_generiraj_demo_jmbg_prefiks_9999():
    j = generiraj_demo_jmbg(1)
    assert j.startswith("9999")
    assert len(j) == 13


def test_sync_opcina_preskoci_praznu(db):
    rez = sync_opcina(db, "TestOpcinaNePostojiXYZ", 51.0, dry_run=True, jmbg_offset=0)
    assert rez["preskoceno"] is True
    assert rez["ukupno"] == 0


@pytest.mark.integration
def test_seed_demo_iskoristivost_integracija(client, db, admin_token):
    """Postavi demo zauzetost i provjeri /statistike (preskoči ako nema inventara)."""
    for naziv, _ in DEMO_CILJEVI:
        uk = db.execute(
            text(
                """
                SELECT COUNT(*)::int
                FROM msisdn m
                JOIN rasponi r ON r.id = m.raspon_id
                JOIN uredjaji u ON u.id = r.uredjaj_id
                JOIN lokacije l ON l.id = u.lokacija_id
                JOIN opcine o ON o.id = l.opcina_id
                WHERE o.naziv = :n
                """
            ),
            {"n": naziv},
        ).scalar()
        if not uk:
            pytest.skip(f"Nema MSISDN u općini {naziv}")

    try:
        sync_opcina(
            db,
            "Goražde",
            51.0,
            dry_run=False,
            jmbg_offset=TEST_JMBG_OFFSET_GORAZDE,
        )
        sync_opcina(
            db,
            "Crnići",
            91.0,
            dry_run=False,
            jmbg_offset=TEST_JMBG_OFFSET_CRNICI,
        )
        db.commit()

        res = client.get("/statistike", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        po = {o["naziv"]: o for o in res.json()["po_opcini"]}
        if "Goražde" in po:
            assert 48 <= po["Goražde"]["postotak_zauzetosti"] <= 54
        if "Crnići" in po:
            assert 88 <= po["Crnići"]["postotak_zauzetosti"] <= 94
    finally:
        db.execute(text(TEST_DEMO_CLEANUP))
        db.commit()
