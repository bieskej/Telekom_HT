"""Unit testovi za novu formulu raspon_granice (sn_len)."""
from __future__ import annotations

import pytest

from app.services.rak_import import iter_brojevi, raspon_granice


@pytest.mark.parametrize(
    "ndc,blok,duzina,pocetak,kraj,brojeva",
    [
        ("30", "3049", 8, "30304900", "30304999", 100),
        ("36", "3612", 9, "363612000", "363612999", 1000),
        ("64", "440", 9, "644400000", "644409999", 10_000),
    ],
)
def test_raspon_granice_primjeri(ndc, blok, duzina, pocetak, kraj, brojeva):
    p, k = raspon_granice(ndc, blok, duzina)
    assert p == pocetak
    assert k == kraj
    assert len(list(iter_brojevi(p, k))) == brojeva


def test_raspon_granice_sn_len_2_daje_100():
    p, k = raspon_granice("30", "3049", 8)
    assert len(list(iter_brojevi(p, k))) == 100


def test_raspon_granice_sn_len_3_daje_1000():
    p, k = raspon_granice("36", "3612", 9)
    assert len(list(iter_brojevi(p, k))) == 1000


def test_raspon_granice_sn_len_4_daje_10000():
    p, k = raspon_granice("64", "440", 9)
    assert len(list(iter_brojevi(p, k))) == 10_000


def test_raspon_granice_preskoceni_kad_sn_len_nula():
    with pytest.raises(ValueError, match="sn_len"):
        raspon_granice("30", "3049", 6)


def test_raspon_granice_preskoceni_kad_duzina_preko_9():
    with pytest.raises(ValueError, match="E.164"):
        raspon_granice("30", "3049", 10)
