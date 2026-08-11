"""Provjera HT centrala – realni primjeri 036... moraju biti unutar plana."""
from __future__ import annotations

from app.services.centrale_plan import (
    CENTRALE_PO_OPCINI,
    Centrala,
    centrale_za,
    kapacitet_neskalirani,
    skaliraj_centrale_na_target,
)


def _broj_je_u_centralama(broj: str, centrale: list[Centrala]) -> bool:
    """Provjeri pripada li broj jednoj od centrala (NDC + prva 3 SN podudaranja)."""
    for c in centrale:
        prefiks = c.ndc + c.prefiks
        if broj.startswith(prefiks):
            return True
    return False


def test_stolac_realni_brojevi_u_planu():
    centrale = centrale_za("Stolac")
    assert _broj_je_u_centralama("36853474", centrale)
    assert _broj_je_u_centralama("36854432", centrale)
    assert _broj_je_u_centralama("36853101", centrale)


def test_mostar_realni_brojevi_u_planu():
    centrale = centrale_za("Mostar")
    assert _broj_je_u_centralama("36325720", centrale)
    assert _broj_je_u_centralama("36336821", centrale)
    assert _broj_je_u_centralama("36395000", centrale)


def test_capljina_realni_brojevi_u_planu():
    centrale = centrale_za("Čapljina")
    assert _broj_je_u_centralama("36805052", centrale)
    assert _broj_je_u_centralama("36805060", centrale)
    assert _broj_je_u_centralama("36805681", centrale)


def test_konjic_realni_brojevi_u_planu():
    centrale = centrale_za("Konjic")
    assert _broj_je_u_centralama("36729813", centrale)
    assert _broj_je_u_centralama("36735370", centrale)


def test_neum_realni_broj_u_planu():
    centrale = centrale_za("Neum")
    assert _broj_je_u_centralama("36880094", centrale)


def test_sve_centrale_hnz_imaju_ndc_36():
    hnz_op = ["Mostar", "Stolac", "Čapljina", "Konjic", "Jablanica",
              "Prozor", "Čitluk", "Neum", "Ravno"]
    for op in hnz_op:
        assert centrale_za(op), f"{op} nema centrala"
        for c in centrale_za(op):
            assert c.ndc == "36", f"{op}: NDC {c.ndc} nije 36"


def test_sarajevo_ima_ndc_33():
    for c in centrale_za("Sarajevo"):
        assert c.ndc == "33"


def test_banja_luka_ima_ndc_51():
    for c in centrale_za("Banja Luka"):
        assert c.ndc == "51"


def test_brcko_ima_ndc_49():
    for c in centrale_za("Brčko"):
        assert c.ndc == "49"


def test_centrala_kapacitet_1000():
    c = CENTRALE_PO_OPCINI["Stolac"][0]
    pocetak = int(c.pocetak())
    kraj = int(c.kraj())
    assert kraj - pocetak + 1 == 1000


def test_skaliranje_na_600k_unutar_5posto():
    skala = skaliraj_centrale_na_target(600_000)
    ukupno = sum(n * 1000 for n in skala.values())
    assert 570_000 <= ukupno <= 630_000, f"Skala van okvira: {ukupno}"


def test_skaliranje_garantira_minimum_jedna_centrala():
    skala = skaliraj_centrale_na_target(10_000)
    for op, n in skala.items():
        assert n >= 1, f"{op}: 0 centrala nakon skaliranja"


def test_kapacitet_neskalirani_najmanje_2M():
    """Plan mora biti dovoljno velik da skala na 600k radi."""
    ukupno = sum(kapacitet_neskalirani(op) for op in CENTRALE_PO_OPCINI)
    assert ukupno >= 2_000_000
