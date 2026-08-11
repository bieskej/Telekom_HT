"""Populacijski podaci po općinama u BiH (popis 2013, javni podaci).

Koristi se za proporcionalnu raspodjelu inventara MSISDN-a tako da realniji broj
brojeva prati stvarni broj stanovnika. Mostar (~105k) dobiva nekoliko slotova,
Stolac (~14k) manje, Neum (~4.6k) najmanje – ali svi imaju > 0.

Izvor: Popis stanovništva BiH 2013 (Agencija za statistiku BiH, javno objavljeno).
Brojke su zaokružene na cijele tisuće radi čitljivosti i lakše raspodjele.
"""
from __future__ import annotations

POPULACIJA: dict[str, int] = {
    # HNŽ
    "Mostar": 105000,
    "Konjic": 25000,
    "Čapljina": 24000,
    "Čitluk": 18000,
    "Stolac": 14000,
    "Prozor": 14000,
    "Jablanica": 9000,
    "Neum": 5000,
    "Ravno": 3000,
    "Crnići": 1000,
    "Hodovo": 800,
    # ZHŽ
    "Široki Brijeg": 29000,
    "Ljubuški": 28000,
    "Posušje": 21000,
    "Grude": 16000,
    # HBŽ
    "Livno": 34000,
    "Tomislavgrad": 32000,
    "Kupres": 5000,
    "Glamoč": 4000,
    "Drvar": 7000,
    "Bosansko Grahovo": 2000,
    # KS
    "Sarajevo": 275000,
    # TK
    "Tuzla": 111000,
    # ZDŽ
    "Zenica": 111000,
    # SBŽ
    "Travnik": 53000,
    "Bugojno": 31000,
    "Jajce": 27000,
    "Vitez": 26000,
    "Novi Travnik": 23000,
    "Kiseljak": 22000,
    "Busovača": 17000,
    "Kreševo": 6000,
    # BPŽ
    "Goražde": 25000,
    # USŽ
    "Bihać": 56000,
    # ŽP
    "Odžak": 19000,
    "Orašje": 19000,
    "Domaljevac": 5000,
    # Brčko (Distrikt)
    "Brčko": 83000,
    # RS – samo Banja Luka prema prioritetu korisnika
    "Banja Luka": 185000,
}


def populacija_za(naziv: str) -> int:
    return POPULACIJA.get(naziv, 1000)


def ukupna_populacija(nazivi: list[str]) -> int:
    return sum(populacija_za(n) for n in nazivi)


def izracunaj_kvote(nazivi: list[str], ukupno_brojeva: int) -> dict[str, int]:
    """Vrati broj MSISDN-a po općini proporcionalan populaciji.

    Garantira minimum 100 po općini i da je suma kvota ≈ `ukupno_brojeva`.
    """
    pop = {n: populacija_za(n) for n in nazivi}
    total_pop = sum(pop.values()) or 1
    kvote: dict[str, int] = {}
    for n, p in pop.items():
        kv = int(round(p / total_pop * ukupno_brojeva))
        kvote[n] = max(kv, 100)
    return kvote
