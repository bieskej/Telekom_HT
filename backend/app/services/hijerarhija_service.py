from sqlalchemy import text
from sqlalchemy.orm import Session

ENTITET_ORDER = ("FBiH", "RS", "Brčko")


def hijerarhija_tree(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                z.entitet,
                z.id AS zupanija_id,
                z.naziv AS zupanija_naziv,
                z.oznaka AS zupanija_oznaka,
                o.id AS opcina_id,
                o.naziv AS opcina_naziv,
                o.tip_jedinice,
                COUNT(*) FILTER (WHERE l.tip = 'postanski_ured')::int AS broj_postanskih,
                COUNT(*) FILTER (WHERE l.tip = 'prodajno_mjesto')::int AS broj_lokacija_ht
            FROM zupanije z
            LEFT JOIN opcine o ON o.zupanija_id = z.id
            LEFT JOIN lokacije l ON l.opcina_id = o.id
            GROUP BY z.entitet, z.id, z.naziv, z.oznaka, o.id, o.naziv, o.tip_jedinice
            ORDER BY z.entitet, z.naziv, o.naziv
            """
        )
    ).fetchall()

    by_entitet: dict[str, dict] = {}
    for r in rows:
        ent = r.entitet or "FBiH"
        if ent not in by_entitet:
            by_entitet[ent] = {"entitet": ent, "zupanije": {}}
        zup_map = by_entitet[ent]["zupanije"]
        zid = r.zupanija_id
        if zid not in zup_map:
            zup_map[zid] = {
                "id": zid,
                "naziv": r.zupanija_naziv,
                "oznaka": r.zupanija_oznaka,
                "opcine": [],
            }
        if r.opcina_id is None:
            continue
        zup_map[zid]["opcine"].append(
            {
                "id": r.opcina_id,
                "naziv": r.opcina_naziv,
                "tip_jedinice": r.tip_jedinice,
                "broj_postanskih": r.broj_postanskih or 0,
                "broj_lokacija_ht": r.broj_lokacija_ht or 0,
            }
        )

    result = []
    for ent in ENTITET_ORDER:
        if ent in by_entitet:
            zups = list(by_entitet[ent]["zupanije"].values())
            for z in zups:
                z["opcine"].sort(key=lambda x: x["naziv"] or "")
            zups.sort(key=lambda x: x["naziv"])
            result.append({"entitet": ent, "zupanije": zups})
    for ent, data in by_entitet.items():
        if ent not in ENTITET_ORDER:
            result.append(
                {
                    "entitet": ent,
                    "zupanije": list(data["zupanije"].values()),
                }
            )
    return result


def hijerarhija_opcina_detail(db: Session, opcina_id: int) -> dict | None:
    opcina = db.execute(
        text(
            """
            SELECT o.id, o.naziv, o.tip_jedinice, o.entitet, z.naziv AS zupanija_naziv, z.oznaka
            FROM opcine o
            JOIN zupanije z ON z.id = o.zupanija_id
            WHERE o.id = :id
            """
        ),
        {"id": opcina_id},
    ).fetchone()
    if not opcina:
        return None

    postanski = db.execute(
        text(
            """
            SELECT id, naziv, postanski_broj, posta_operater
            FROM lokacije
            WHERE opcina_id = :o AND tip = 'postanski_ured'
            ORDER BY postanski_broj, naziv
            """
        ),
        {"o": opcina_id},
    ).fetchall()

    lokacije_ht = db.execute(
        text(
            """
            SELECT id, naziv, tip
            FROM lokacije
            WHERE opcina_id = :o AND tip <> 'postanski_ured'
            ORDER BY naziv
            """
        ),
        {"o": opcina_id},
    ).fetchall()

    ht_out = []
    for loc in lokacije_ht:
        uredjaji = db.execute(
            text(
                """
                SELECT u.id, u.tip, u.oznaka
                FROM uredjaji u
                WHERE u.lokacija_id = :l
                ORDER BY u.oznaka
                """
            ),
            {"l": loc.id},
        ).fetchall()
        u_list = []
        for u in uredjaji:
            rasponi = db.execute(
                text(
                    """
                    SELECT
                        r.id, r.pocetak, r.kraj,
                        COUNT(m.id)::int AS msisdn_ukupno,
                        COUNT(*) FILTER (WHERE m.status = 'zauzet')::int AS zauzet,
                        COUNT(*) FILTER (WHERE m.status = 'slobodan')::int AS slobodan
                    FROM rasponi r
                    LEFT JOIN msisdn m ON m.raspon_id = r.id
                    WHERE r.uredjaj_id = :u
                    GROUP BY r.id, r.pocetak, r.kraj
                    ORDER BY r.pocetak
                    """
                ),
                {"u": u.id},
            ).fetchall()
            u_list.append(
                {
                    "id": u.id,
                    "tip": u.tip,
                    "oznaka": u.oznaka,
                    "rasponi": [
                        {
                            "id": r.id,
                            "pocetak": r.pocetak,
                            "kraj": r.kraj,
                            "msisdn_ukupno": r.msisdn_ukupno,
                            "zauzet": r.zauzet,
                            "slobodan": r.slobodan,
                        }
                        for r in rasponi
                    ],
                }
            )
        ht_out.append({"id": loc.id, "naziv": loc.naziv, "tip": loc.tip, "uredjaji": u_list})

    return {
        "opcina": {
            "id": opcina.id,
            "naziv": opcina.naziv,
            "tip_jedinice": opcina.tip_jedinice,
            "entitet": opcina.entitet,
            "zupanija_naziv": opcina.zupanija_naziv,
            "zupanija_oznaka": opcina.oznaka,
        },
        "postanski_uredi": [
            {
                "id": p.id,
                "naziv": p.naziv,
                "postanski_broj": p.postanski_broj,
                "posta_operater": p.posta_operater,
            }
            for p in postanski
        ],
        "lokacije_ht": ht_out,
    }


def hijerarhija_stablo(db: Session) -> list[dict]:
    """Vraća kompletno stablo Županija → Općina → Lokacija → MSAN sa
    brojem MSISDN-a na svakoj razini.

    Vraća samo grane koje imaju barem jedan MSISDN (ne vraća prazne
    županije/lokacije bez RAK podataka).
    """
    rows = db.execute(
        text(
            """
            SELECT
                z.id AS zupanija_id,
                z.oznaka AS zupanija_oznaka,
                z.sjediste AS zupanija_sjediste,
                z.entitet AS zupanija_entitet,
                o.id AS opcina_id,
                o.naziv AS opcina_naziv,
                l.id AS lokacija_id,
                l.naziv AS lokacija_naziv,
                u.id AS uredjaj_id,
                u.oznaka AS uredjaj_oznaka,
                u.tip AS uredjaj_tip,
                COUNT(m.id)::int AS msisdn_ukupno,
                COUNT(m.id) FILTER (
                    WHERE m.status = 'slobodan'
                      AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
                )::int AS msisdn_slobodni,
                COUNT(m.id) FILTER (WHERE m.status = 'zauzet')::int AS msisdn_zauzeti,
                COUNT(m.id) FILTER (WHERE m.status = 'karantena')::int AS msisdn_karantena
            FROM zupanije z
            JOIN opcine o ON o.zupanija_id = z.id
            JOIN lokacije l ON l.opcina_id = o.id
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            GROUP BY z.id, z.oznaka, z.sjediste, z.entitet,
                     o.id, o.naziv, l.id, l.naziv, u.id, u.oznaka, u.tip
            ORDER BY z.sjediste, o.naziv, l.naziv, u.oznaka
            """
        )
    ).fetchall()

    z_map: dict[int, dict] = {}
    for r in rows:
        zup = z_map.setdefault(
            r.zupanija_id,
            {
                "tip": "zupanija",
                "id": r.zupanija_id,
                "naziv": r.zupanija_sjediste or r.zupanija_oznaka,
                "oznaka": r.zupanija_oznaka,
                "entitet": r.zupanija_entitet,
                "ukupno": 0,
                "slobodni": 0,
                "zauzeti": 0,
                "karantena": 0,
                "_opcine": {},
            },
        )
        op = zup["_opcine"].setdefault(
            r.opcina_id,
            {
                "tip": "opcina",
                "id": r.opcina_id,
                "naziv": r.opcina_naziv,
                "ukupno": 0,
                "slobodni": 0,
                "zauzeti": 0,
                "karantena": 0,
                "_lokacije": {},
            },
        )
        lok = op["_lokacije"].setdefault(
            r.lokacija_id,
            {
                "tip": "lokacija",
                "id": r.lokacija_id,
                "naziv": r.lokacija_naziv,
                "ukupno": 0,
                "slobodni": 0,
                "zauzeti": 0,
                "karantena": 0,
                "_uredjaji": [],
            },
        )
        lok["_uredjaji"].append(
            {
                "tip": "uredjaj",
                "id": r.uredjaj_id,
                "naziv": r.uredjaj_oznaka,
                "uredjaj_tip": r.uredjaj_tip,
                "ukupno": r.msisdn_ukupno,
                "slobodni": r.msisdn_slobodni,
                "zauzeti": r.msisdn_zauzeti,
                "karantena": r.msisdn_karantena,
            }
        )
        for node in (lok, op, zup):
            node["ukupno"] += r.msisdn_ukupno
            node["slobodni"] += r.msisdn_slobodni
            node["zauzeti"] += r.msisdn_zauzeti
            node["karantena"] += r.msisdn_karantena

    rezultat = []
    for zup in z_map.values():
        opcine = []
        for op in zup["_opcine"].values():
            lokacije = []
            for lok in op["_lokacije"].values():
                lok["uredjaji"] = lok.pop("_uredjaji")
                lokacije.append(lok)
            op["lokacije"] = lokacije
            op.pop("_lokacije")
            opcine.append(op)
        zup["opcine"] = opcine
        zup.pop("_opcine")
        rezultat.append(zup)

    rezultat.sort(key=lambda z: z["naziv"])
    return rezultat


def hijerarhija_cvor_detalj(
    db: Session, tip: str, cvor_id: int, sample_n: int = 10
) -> dict | None:
    """Detalj jednog čvora (županija/općina/lokacija/uređaj):
    - osnovne metrike (ukupno/slobodni/zauzeti/karantena)
    - 10 MSISDN uzoraka
    - link parametri za /brojevi filter
    """
    if tip == "zupanija":
        info = db.execute(
            text(
                """
                SELECT z.id, z.oznaka, z.sjediste, z.entitet
                FROM zupanije z WHERE z.id = :id
                """
            ),
            {"id": cvor_id},
        ).fetchone()
        if not info:
            return None
        where = "z.id = :id"
        params = {"id": cvor_id}
        link_param = None
        naslov = info.sjediste or info.oznaka
        opis = f"Županija {info.oznaka} ({info.entitet})"
    elif tip == "opcina":
        info = db.execute(
            text("SELECT id, naziv FROM opcine WHERE id = :id"),
            {"id": cvor_id},
        ).fetchone()
        if not info:
            return None
        where = "o.id = :id"
        params = {"id": cvor_id}
        link_param = ("opcina_naziv", info.naziv)
        naslov = info.naziv
        opis = "Općina"
    elif tip == "lokacija":
        info = db.execute(
            text("SELECT id, naziv FROM lokacije WHERE id = :id"),
            {"id": cvor_id},
        ).fetchone()
        if not info:
            return None
        where = "l.id = :id"
        params = {"id": cvor_id}
        link_param = ("lokacija_id", str(cvor_id))
        naslov = info.naziv
        opis = "Lokacija"
    elif tip == "uredjaj":
        info = db.execute(
            text("SELECT id, oznaka, tip FROM uredjaji WHERE id = :id"),
            {"id": cvor_id},
        ).fetchone()
        if not info:
            return None
        where = "u.id = :id"
        params = {"id": cvor_id}
        link_param = ("uredjaj_id", str(cvor_id))
        naslov = info.oznaka
        opis = f"Uređaj ({info.tip})"
    else:
        return None

    metrike = db.execute(
        text(
            f"""
            SELECT
                COUNT(m.id)::int AS ukupno,
                COUNT(m.id) FILTER (
                    WHERE m.status = 'slobodan'
                      AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
                )::int AS slobodni,
                COUNT(m.id) FILTER (WHERE m.status = 'zauzet')::int AS zauzeti,
                COUNT(m.id) FILTER (WHERE m.status = 'karantena')::int AS karantena
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            JOIN zupanije z ON z.id = o.zupanija_id
            WHERE {where}
            """
        ),
        params,
    ).fetchone()

    uzorci = db.execute(
        text(
            f"""
            SELECT m.id, m.broj, m.status,
                   COALESCE(k.naziv, 'silver') AS kvaliteta
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            JOIN zupanije z ON z.id = o.zupanija_id
            LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE {where}
            ORDER BY m.broj
            LIMIT :n
            """
        ),
        {**params, "n": sample_n},
    ).fetchall()

    return {
        "tip": tip,
        "id": cvor_id,
        "naslov": naslov,
        "opis": opis,
        "metrike": {
            "ukupno": (metrike.ukupno if metrike else 0) or 0,
            "slobodni": (metrike.slobodni if metrike else 0) or 0,
            "zauzeti": (metrike.zauzeti if metrike else 0) or 0,
            "karantena": (metrike.karantena if metrike else 0) or 0,
        },
        "brojevi_uzorak": [
            {"id": r.id, "broj": r.broj, "status": r.status, "kvaliteta": r.kvaliteta}
            for r in uzorci
        ],
        "filter_param": (
            {"kljuc": link_param[0], "vrijednost": link_param[1]}
            if link_param
            else None
        ),
    }


def hijerarhija_pretraga_pb(db: Session, pb: str) -> dict | None:
    pb = pb.strip()
    if not pb:
        return None
    row = db.execute(
        text(
            """
            SELECT
                l.id AS lokacija_id,
                l.naziv AS lokacija_naziv,
                l.postanski_broj,
                l.posta_operater,
                o.id AS opcina_id,
                o.naziv AS opcina_naziv,
                o.tip_jedinice,
                z.id AS zupanija_id,
                z.naziv AS zupanija_naziv,
                z.oznaka AS zupanija_oznaka,
                z.entitet
            FROM lokacije l
            JOIN opcine o ON o.id = l.opcina_id
            JOIN zupanije z ON z.id = o.zupanija_id
            WHERE l.postanski_broj = :pb AND l.tip = 'postanski_ured'
            LIMIT 1
            """
        ),
        {"pb": pb},
    ).fetchone()
    if not row:
        return None
    return {
        "entitet": row.entitet,
        "zupanija_id": row.zupanija_id,
        "zupanija_naziv": row.zupanija_naziv,
        "zupanija_oznaka": row.zupanija_oznaka,
        "opcina_id": row.opcina_id,
        "opcina_naziv": row.opcina_naziv,
        "tip_jedinice": row.tip_jedinice,
        "lokacija_id": row.lokacija_id,
        "lokacija_naziv": row.lokacija_naziv,
        "postanski_broj": row.postanski_broj,
        "posta_operater": row.posta_operater,
    }
