"""Pooštrena klasifikacija (zadnja 4 znamenke):
  diamond  – zadnje 4 iste (XXXX), monotone 4 (1234/4321), palindrom 4 (1221, 7337).
  platinum – XYYY/YYYX (3+1), ABAB.
  gold     – zadnje 2 iste a prethodna različita (XYY), monotone 3 (234/321).
  silver   – ostalo.
"""
import pytest
from sqlalchemy import text

from app.services.kvaliteta_klasifikacija import klasificiraj_broj, kvaliteta_id_za_broj


@pytest.mark.parametrize(
    "broj",
    [
        "36207777",
        "36850000",
        "33205555",
        "51201111",
    ],
)
def test_diamond_zadnje_4_iste(broj):
    cifre = "".join(c for c in broj if c.isdigit())
    assert len(set(cifre[-4:])) == 1
    assert klasificiraj_broj(broj) == "diamond"


@pytest.mark.parametrize(
    "broj",
    [
        "36201234",
        "36204321",
        "33205678",
        "51209876",
    ],
)
def test_diamond_monotone_4(broj):
    assert klasificiraj_broj(broj) == "diamond"


@pytest.mark.parametrize(
    "broj",
    [
        "36201221",
        "33207337",
        "36202112",
        "51209669",
    ],
)
def test_diamond_palindrom_4(broj):
    cifre = "".join(c for c in broj if c.isdigit())
    z4 = cifre[-4:]
    assert z4 == z4[::-1] and len(set(z4)) > 1
    assert klasificiraj_broj(broj) == "diamond"


@pytest.mark.parametrize(
    "broj",
    [
        "36202111",
        "36201222",
        "33208555",
        "51207333",
    ],
)
def test_platinum_xyyy_ili_yyyx(broj):
    assert klasificiraj_broj(broj) == "platinum"


@pytest.mark.parametrize(
    "broj",
    [
        "36201212",
        "36207373",
        "33203434",
        "51208989",
    ],
)
def test_platinum_abab(broj):
    assert klasificiraj_broj(broj) == "platinum"


@pytest.mark.parametrize(
    "broj",
    [
        "36201266",
        "36208533",
        "33208077",
        "51209188",
    ],
)
def test_gold_xyy_zadnje_2_iste(broj):
    cifre = "".join(c for c in broj if c.isdigit())
    z4 = cifre[-4:]
    assert z4[2] == z4[3] and z4[1] != z4[2]
    assert klasificiraj_broj(broj) == "gold"


@pytest.mark.parametrize(
    "broj",
    [
        "36209234",
        "36201321",
        "33208456",
        "51209765",
    ],
)
def test_gold_monotone_3_na_kraju(broj):
    assert klasificiraj_broj(broj) == "gold"


@pytest.mark.parametrize(
    "broj",
    [
        "36325720",
        "36853474",
        "36805052",
        "36729813",
        "36880094",
    ],
)
def test_silver_realni_ht_primjeri(broj):
    """Stvarni HT brojevi iz mreže – treba biti silver (običan završetak)."""
    assert klasificiraj_broj(broj) == "silver"


def test_diamond_ima_prioritet_nad_platinum():
    assert klasificiraj_broj("36207777") == "diamond"
    assert klasificiraj_broj("36202111") == "platinum"


def test_gold_nije_diamond_ni_platinum():
    """36 200 1266: zadnje 4 = "1266", c=6 d=6 b=2 a=1 → gold (XYY)."""
    assert klasificiraj_broj("36201266") == "gold"


def test_prazan_broj_silver():
    assert klasificiraj_broj("") == "silver"
    assert klasificiraj_broj("+387") == "silver"


def test_format_s_razmacima_i_plusem():
    assert klasificiraj_broj("+387 36 207 777") == "diamond"
    assert klasificiraj_broj("+387 36 325 720") == "silver"


def test_kvaliteta_id_za_broj(db):
    silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()
    gold_id_ocek = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one()
    assert kvaliteta_id_za_broj(db, "36325720") == silver_id
    assert kvaliteta_id_za_broj(db, "36201266") == gold_id_ocek
