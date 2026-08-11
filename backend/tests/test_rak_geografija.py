"""Testovi za geografsku raspodjelu po županiji (rak_geografija)."""
from __future__ import annotations

from app.services.rak_geografija import (
    OpcinaGeo,
    NDC_BEZ_RASPODJELE,
    NDC_OPCINA_FALLBACK,
    odredi_listu_opcina,
    odredi_primarnu_opcinu,
    opcine_za_zupaniju,
    slug_opcina,
    ucitaj_opcine_master,
)


def test_master_sadrzi_hnz_opcine():
    master = ucitaj_opcine_master()
    nazivi = {o.naziv for o in master if o.zupanija_oznaka == "HNŽ"}
    for ime in ["Mostar", "Stolac", "Čapljina", "Čitluk", "Neum", "Konjic", "Jablanica"]:
        assert ime in nazivi, f"Nedostaje općina {ime} u HNŽ master CSV-u."


def test_primarna_opcina_iz_ndc_fallbacka():
    master = ucitaj_opcine_master()
    primarna = odredi_primarnu_opcinu("36", "3612", None, {}, master)
    assert primarna.naziv == "Mostar"
    assert primarna.zupanija_oznaka == "HNŽ"


def test_raspodjela_hnz_ukljucuje_capljinu_i_stolac():
    master = ucitaj_opcine_master()
    primarna = NDC_OPCINA_FALLBACK["36"]
    geo = OpcinaGeo(primarna[0], primarna[1], primarna[2])
    lista = odredi_listu_opcina("36", geo, master)
    nazivi = {o.naziv for o in lista}
    assert "Mostar" in nazivi
    assert "Čapljina" in nazivi
    assert "Stolac" in nazivi
    assert "Neum" in nazivi
    assert lista[0].naziv == "Mostar"


def test_ndc_49_ostaje_samo_brcko():
    master = ucitaj_opcine_master()
    geo = OpcinaGeo("Brčko", "BRC", "Brčko")
    lista = odredi_listu_opcina("49", geo, master)
    assert len(lista) == 1
    assert lista[0].naziv == "Brčko"
    assert "49" in NDC_BEZ_RASPODJELE


def test_ndc_51_ostaje_samo_banja_luka():
    master = ucitaj_opcine_master()
    geo = OpcinaGeo("Banja Luka", "RS-BL", "RS")
    lista = odredi_listu_opcina("51", geo, master)
    assert len(lista) == 1
    assert lista[0].naziv == "Banja Luka"


def test_slug_opcina_dijakritici():
    assert slug_opcina("Čapljina") == "CAPLJINA"
    assert slug_opcina("Široki Brijeg") == "SIROKI_BRIJEG"
    assert slug_opcina("Mostar") == "MOSTAR"


def test_opcine_za_zupaniju_hnz_nije_prazno():
    master = ucitaj_opcine_master()
    hnz = opcine_za_zupaniju(master, "HNŽ")
    assert len(hnz) >= 8
