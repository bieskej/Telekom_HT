"""Popuni `opcine.lat` i `opcine.lon` za općine HT Eronet mreže.

Koordinate (WGS84) su prikupljene iz javnih izvora:
- Wikipedia infobox geo koordinate (gradovi BiH)
- OpenStreetMap Nominatim za manja mjesta (Crnići, Hodovo, Domaljevac…)

Skripta je idempotentna: koristi UPDATE samo nad postojećim općinama,
ne stvara nove redove. Pokreni:

    python -m scripts.seed_opcine_geo

TODO: zamijeniti pojednostavljene koordinate s pravim centroidima granica
iz GADM/OSM Boundaries kad budemo imali polygon geometriju (Faza 1+).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed_opcine_geo")


KOORDINATE: dict[str, tuple[float, float]] = {
    # ── HNŽ (NDC 36) ───────────────────────────────────────────────────
    "Mostar": (43.3438, 17.8078),
    "Stolac": (43.0838, 17.9569),
    "Čapljina": (43.1167, 17.6831),
    "Konjic": (43.6500, 17.9586),
    "Jablanica": (43.6614, 17.7619),
    "Prozor": (43.8231, 17.6125),
    "Čitluk": (43.2236, 17.7019),
    "Neum": (42.9242, 17.6128),
    "Ravno": (42.8786, 17.8794),
    "Crnići": (43.1750, 17.7700),
    "Hodovo": (43.1500, 17.9050),

    # ── KS (NDC 33) ────────────────────────────────────────────────────
    "Sarajevo": (43.8563, 18.4131),

    # ── TK (NDC 35) ────────────────────────────────────────────────────
    "Tuzla": (44.5384, 18.6763),

    # ── ZDŽ (NDC 32) ───────────────────────────────────────────────────
    "Zenica": (44.2010, 17.9075),

    # ── RS-BL (NDC 51) ─────────────────────────────────────────────────
    "Banja Luka": (44.7722, 17.1910),

    # ── HBŽ (NDC 34) ───────────────────────────────────────────────────
    "Livno": (43.8250, 17.0070),
    "Tomislavgrad": (43.7167, 17.2247),
    "Kupres": (43.9803, 17.2778),
    "Glamoč": (43.9444, 16.8439),
    "Drvar": (44.3736, 16.3833),
    "Bosansko Grahovo": (44.1822, 16.3597),

    # ── SBŽ (NDC 30) ───────────────────────────────────────────────────
    "Travnik": (44.2264, 17.6658),
    "Bugojno": (44.0581, 17.4500),
    "Jajce": (44.3431, 17.2706),
    "Vitez": (44.1556, 17.7972),
    "Busovača": (44.0833, 17.8833),
    "Novi Travnik": (44.1717, 17.6608),
    "Kiseljak": (43.9389, 18.0808),
    "Kreševo": (43.8678, 18.0481),

    # ── USŽ (NDC 37) ───────────────────────────────────────────────────
    "Bihać": (44.8169, 15.8708),

    # ── BPŽ (NDC 38) ───────────────────────────────────────────────────
    "Goražde": (43.6675, 18.9764),

    # ── ZHŽ (NDC 39) ───────────────────────────────────────────────────
    "Široki Brijeg": (43.3832, 17.5946),
    "Grude": (43.4081, 17.4144),
    "Ljubuški": (43.1972, 17.5500),
    "Posušje": (43.4731, 17.3306),

    # ── ŽP (NDC 31) ────────────────────────────────────────────────────
    "Orašje": (45.0336, 18.6960),
    "Odžak": (45.0292, 18.3050),
    "Domaljevac": (45.0633, 18.4322),

    # ── BRC (NDC 49) ───────────────────────────────────────────────────
    "Brčko": (44.8694, 18.8103),
}


def popuni_koordinate() -> dict:
    db = SessionLocal()
    try:
        azurirano = 0
        nepoznato: list[str] = []
        nedostaje: list[str] = []

        postojeca: dict[str, list[int]] = {}
        for row in db.execute(text("SELECT id, naziv FROM opcine")).fetchall():
            postojeca.setdefault(row.naziv, []).append(row.id)

        for naziv, (lat, lon) in KOORDINATE.items():
            if naziv not in postojeca:
                nepoznato.append(naziv)
                continue
            res = db.execute(
                text("UPDATE opcine SET lat = :lat, lon = :lon WHERE naziv = :naziv"),
                {"lat": lat, "lon": lon, "naziv": naziv},
            )
            azurirano += res.rowcount or 0

        opcine_s_brojevima = db.execute(
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
        nedostaje = [r.naziv for r in opcine_s_brojevima]

        db.commit()
        return {
            "azurirano": azurirano,
            "nepoznato_u_bazi": nepoznato,
            "opcine_s_brojevima_bez_koordinata": nedostaje,
        }
    finally:
        db.close()


def main() -> int:
    rez = popuni_koordinate()
    log.info("Ažurirano općina: %s", rez["azurirano"])
    if rez["nepoznato_u_bazi"]:
        log.warning(
            "Općine iz KOORDINATE rječnika ne postoje u bazi: %s",
            ", ".join(rez["nepoznato_u_bazi"]),
        )
    if rez["opcine_s_brojevima_bez_koordinata"]:
        log.warning(
            "Općine s brojevima nemaju koordinate: %s",
            ", ".join(rez["opcine_s_brojevima_bez_koordinata"]),
        )
        return 1
    log.info("Sve općine s brojevima imaju koordinate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
