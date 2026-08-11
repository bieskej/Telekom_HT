"""Klasifikacija MSISDN po uzorku **zadnjih 4 znamenki** (pretplatnički završetak).

Pravila gledaju isključivo SN završetak jer korisnici biraju "lijep završni
broj" – NDC i centrala su geografski, ne uljepšavaju broj.

Prioritet (prvi koji zadovolji):
  diamond   – zadnje 4 iste (XXXX);
              ili zadnje 4 = 1234 ili 4321;
              ili palindromsko zadnje 4 (npr. 1221, 7337) različitih znamenki.
  platinum  – zadnje 3 iste + 4. različita (XYYY ili YYYX, npr. 3222, 2228);
              ili zadnje 4 = ABAB s različitim A i B (1212, 7373).
  gold      – zadnje 2 iste i pre-prethodna različita (XYY, npr. ...4 55);
              ili zadnje 3 = monotone rastuće/padajuće (234, 567, 654, 321).
  silver    – sve ostalo (default, najjeftiniji).

Očekivane distribucije za nasumičan završetak:
  diamond  ≈ 0.5 %    (10/10000 isto + 2/10000 monotone 4 + ~38/10000 palindrom)
  platinum ≈ 1.6 %    (~90 pat. XYYY + ~72 ABAB)
  gold     ≈ 9 %      (~9 % zadnje 2 iste i nije XYY platinum; + monotone 3)
  silver   ≈ 89 %     (ostatak)
"""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

_KVALITETE = ("diamond", "platinum", "gold", "silver")
_MONOTONE_4 = ("0123", "1234", "2345", "3456", "4567", "5678", "6789",
               "9876", "8765", "7654", "6543", "5432", "4321", "3210")
_MONOTONE_3 = ("012", "123", "234", "345", "456", "567", "678", "789",
               "987", "876", "765", "654", "543", "432", "321", "210")


def _samo_znamenke(broj: str) -> str:
    return re.sub(r"\D", "", broj or "")


def _zadnje_4(cifre: str) -> str:
    return cifre[-4:] if len(cifre) >= 4 else cifre


def _zadnje_3(cifre: str) -> str:
    return cifre[-3:] if len(cifre) >= 3 else cifre


def _je_diamond(cifre: str) -> bool:
    z4 = _zadnje_4(cifre)
    if len(z4) < 4:
        return False
    if len(set(z4)) == 1:
        return True
    if z4 in _MONOTONE_4:
        return True
    if z4 == z4[::-1] and len(set(z4)) > 1:
        return True
    return False


def _je_platinum(cifre: str) -> bool:
    z4 = _zadnje_4(cifre)
    if len(z4) < 4:
        return False
    a, b, c, d = z4[0], z4[1], z4[2], z4[3]
    if b == c == d and a != b:
        return True
    if a == b == c and a != d:
        return True
    if a == c and b == d and a != b:
        return True
    return False


def _je_gold(cifre: str) -> bool:
    z4 = _zadnje_4(cifre)
    if len(z4) >= 4:
        a, b, c, d = z4[0], z4[1], z4[2], z4[3]
        if c == d and b != c:
            return True
    z3 = _zadnje_3(cifre)
    if z3 in _MONOTONE_3:
        return True
    return False


def klasificiraj_broj(broj: str) -> str:
    """Vraća naziv kvalitete za broj (samo znamenke, bez +387 i razmaka)."""
    cifre = _samo_znamenke(broj)
    if not cifre:
        return "silver"
    if _je_diamond(cifre):
        return "diamond"
    if _je_platinum(cifre):
        return "platinum"
    if _je_gold(cifre):
        return "gold"
    return "silver"


def kvaliteta_id_za_broj(db: Session, broj: str) -> int:
    naziv = klasificiraj_broj(broj)
    row = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = :n"), {"n": naziv}).scalar_one()
    return int(row)


__all__ = ["klasificiraj_broj", "kvaliteta_id_za_broj", "_KVALITETE"]
