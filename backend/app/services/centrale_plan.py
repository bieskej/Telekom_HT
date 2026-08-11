"""Plan numeriranja fiksne telefonije HT Eronet po općinama.

Format MSISDN: 8 znamenki = NDC(2) + CENTRALA(3) + PRETPLATNIK(3).
Prikaz: +387 36 853 474.

NDC po županijama (RAK Plan numeriranja BiH):
    30 SBŽ   31 ŽP    32 ZDŽ   33 KS    34 HBŽ   35 TK
    36 HNŽ   37 USŽ   38 BPŽ   39 ZHŽ   49 BRC   51 RS-BL

Centrale za HNŽ (NDC 36) su preuzete iz javno dostupnih izvora HT Eroneta i
službenih web stranica općina – usklađene s realnim primjerima:
    Stolac    036 853 474, 036 854 432, 036 853 101 → 850-869
    Mostar    036 325 720, 036 336 821, 036 395 000 → 200-499 (200, 300, 390)
    Konjic    036 726 215, 036 729 813, 036 735 370 → 700-749
    Jablanica 036 751 300, 036 752 651            → 750-769
    Prozor    036 771 910, 036 771 936            → 770-789
    Čitluk    036 640 500, 036 640 537            → 640-679
    Čapljina  036 805 052, 036 805 060, 036 805 681 → 800-839
    Neum      036 880 094, 036 880 581            → 880-884
    Ravno     036 891 465                          → 890-891

Ostale županije: aproksimirane prema HT logici (Mostar/Sarajevo/Banja Luka glavni
pool, ostatak proporcionalno populaciji).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Centrala:
    """Jedna centrala = `prefiks_3` znamenke iza NDC-a, kapacitet 1000 brojeva.

    Brojevi unutar centrale: `f"{ndc}{prefiks_3}{000-999}"`.
    """

    ndc: str
    prefiks: str

    def pocetak(self) -> str:
        return f"{self.ndc}{self.prefiks}000"

    def kraj(self) -> str:
        return f"{self.ndc}{self.prefiks}999"


def _opseg(ndc: str, od: int, do_uklj: int) -> list[Centrala]:
    """Generiraj listu centrala od `od` do `do_uklj` (uključivo)."""
    out: list[Centrala] = []
    for n in range(od, do_uklj + 1):
        out.append(Centrala(ndc, f"{n:03d}"))
    return out


def _pojedine(ndc: str, prefiksi: list[int]) -> list[Centrala]:
    return [Centrala(ndc, f"{p:03d}") for p in prefiksi]


CENTRALE_PO_OPCINI: dict[str, list[Centrala]] = {
    # ── HNŽ (NDC 36) – stvarne HT centrale ─────────────────────────────────
    "Mostar": _opseg("36", 200, 499),       # 300 centrala × 1000 = 300 000 (skalirat se)
    "Čitluk": _opseg("36", 640, 679),       # 40 → 40 000
    "Konjic": _opseg("36", 700, 749),       # 50 → 50 000
    "Jablanica": _opseg("36", 750, 769),    # 20 → 20 000
    "Prozor": _opseg("36", 770, 789),       # 20 → 20 000
    "Čapljina": _opseg("36", 800, 839),     # 40 → 40 000
    "Stolac": _opseg("36", 850, 869),       # 20 → 20 000
    "Neum": _opseg("36", 880, 884),         # 5  → 5 000
    "Ravno": _opseg("36", 890, 891),        # 2  → 2 000
    "Crnići": _opseg("36", 887, 887),       # 1  → 1 000
    "Hodovo": _opseg("36", 888, 888),       # 1  → 1 000

    # ── KS (NDC 33) – Sarajevo dominira ────────────────────────────────────
    "Sarajevo": _opseg("33", 200, 699),     # 500 → 500 000

    # ── TK (NDC 35) ────────────────────────────────────────────────────────
    "Tuzla": _opseg("35", 200, 399),        # 200 → 200 000

    # ── ZDŽ (NDC 32) ───────────────────────────────────────────────────────
    "Zenica": _opseg("32", 200, 349),       # 150 → 150 000

    # ── RS-BL (NDC 51) – samo Banja Luka ───────────────────────────────────
    "Banja Luka": _opseg("51", 200, 449),   # 250 → 250 000

    # ── HBŽ (NDC 34) ───────────────────────────────────────────────────────
    "Livno": _opseg("34", 200, 249),
    "Tomislavgrad": _opseg("34", 300, 329),
    "Kupres": _opseg("34", 350, 354),
    "Glamoč": _opseg("34", 360, 363),
    "Drvar": _opseg("34", 370, 374),
    "Bosansko Grahovo": _opseg("34", 380, 381),

    # ── SBŽ (NDC 30) ───────────────────────────────────────────────────────
    "Bugojno": _opseg("30", 250, 289),
    "Travnik": _opseg("30", 500, 549),
    "Jajce": _opseg("30", 600, 649),
    "Vitez": _opseg("30", 700, 729),
    "Busovača": _opseg("30", 730, 749),
    "Novi Travnik": _opseg("30", 750, 779),
    "Kiseljak": _opseg("30", 800, 829),
    "Kreševo": _opseg("30", 830, 839),

    # ── USŽ (NDC 37) ───────────────────────────────────────────────────────
    "Bihać": _opseg("37", 200, 279),        # 80 → 80 000

    # ── BPŽ (NDC 38) ───────────────────────────────────────────────────────
    "Goražde": _opseg("38", 200, 249),

    # ── ZHŽ (NDC 39) ───────────────────────────────────────────────────────
    "Široki Brijeg": _opseg("39", 700, 729),
    "Grude": _opseg("39", 800, 819),
    "Ljubuški": _opseg("39", 830, 859),
    "Posušje": _opseg("39", 670, 689),

    # ── ŽP (NDC 31) ────────────────────────────────────────────────────────
    "Orašje": _opseg("31", 700, 739),
    "Odžak": _opseg("31", 760, 789),
    "Domaljevac": _opseg("31", 790, 794),

    # ── BRC (NDC 49) ───────────────────────────────────────────────────────
    "Brčko": _opseg("49", 200, 289),        # 90 → 90 000
}


GARANTIRANE_CENTRALE: dict[str, list[str]] = {
    "Mostar":    ["325", "336", "395", "200", "300", "400"],
    "Stolac":    ["853", "854", "850"],
    "Čapljina":  ["805", "800"],
    "Konjic":    ["729", "735", "700"],
    "Neum":      ["880"],
}


def centrale_za(opcina: str) -> list[Centrala]:
    return CENTRALE_PO_OPCINI.get(opcina, [])


def garantirane_za(opcina: str) -> list[Centrala]:
    """Centrale koje moraju biti u skali (realni HT primjeri)."""
    ndc_op = {c.prefiks: c for c in centrale_za(opcina)}
    return [ndc_op[p] for p in GARANTIRANE_CENTRALE.get(opcina, []) if p in ndc_op]


def kapacitet_neskalirani(opcina: str) -> int:
    return len(centrale_za(opcina)) * 1000


def skaliraj_centrale_na_target(target_total: int) -> dict[str, int]:
    """Skalira broj centrala po općini tako da ukupno ≈ `target_total` brojeva.

    Vraća: opcina → broj centrala (cijeli broj). Garantira minimum 1 centrala
    za svaku općinu iz mape.
    """
    neskalirano_po_op = {op: len(c) for op, c in CENTRALE_PO_OPCINI.items()}
    ukupno = sum(neskalirano_po_op.values()) * 1000
    if ukupno == 0:
        return {op: 0 for op in neskalirano_po_op}

    faktor = target_total / ukupno
    out: dict[str, int] = {}
    for op, n_centrala in neskalirano_po_op.items():
        skaliran = max(1, int(round(n_centrala * faktor)))
        out[op] = skaliran
    return out
