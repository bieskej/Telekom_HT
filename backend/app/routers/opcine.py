from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled
from app.database import get_db
from app.schemas import OpcinaResponse
from app.services import catalog_service

router = APIRouter(tags=["opcine"])

GEOJSON_BBOX_DELTA = 0.04


@router.get("/opcine", response_model=list[OpcinaResponse])
async def lista_opcina(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
    samo_s_brojevima: bool = Query(False, description="Samo općine s MSISDN u RAK lancu"),
    pretraga: str | None = Query(None, description="Filtriraj po nazivu općine (djelomično)"),
):
    if samo_s_brojevima:
        rows = catalog_service.lista_opcina_sa_brojevima(db, pretraga)
        return [OpcinaResponse(**r) for r in rows]

    rows = catalog_service.lista_opcina_sve_sa_brojkom(db, pretraga)
    return [OpcinaResponse(**r) for r in rows]


@router.get("/opcine/geojson")
async def opcine_geojson(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    """GeoJSON FeatureCollection za choropleth mapu općina.

    Geometrija je pojednostavljen bbox (±0.04° ≈ 4.4 km) oko centroida.
    TODO: zamijeniti pravim granicama iz GADM/OSM Boundaries (Polygon).
    """
    rows = db.execute(
        text(
            """
            SELECT o.naziv,
                   MAX(o.lat) AS lat,
                   MAX(o.lon) AS lon,
                   COUNT(m.id) AS ukupno,
                   COUNT(m.id) FILTER (
                     WHERE m.status = 'slobodan'
                       AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
                   ) AS slobodni,
                   COUNT(m.id) FILTER (WHERE m.status IN ('zauzet','karantena')) AS zauzeto_karantena
            FROM opcine o
            JOIN lokacije l ON l.opcina_id = o.id
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            WHERE o.lat IS NOT NULL AND o.lon IS NOT NULL
            GROUP BY o.naziv
            ORDER BY o.naziv
            """
        )
    ).fetchall()

    d = GEOJSON_BBOX_DELTA
    features = []
    for r in rows:
        uk = r.ukupno or 0
        zk = r.zauzeto_karantena or 0
        postotak = round((zk / uk) * 100, 2) if uk else 0.0
        lat = float(r.lat)
        lon = float(r.lon)
        polygon = [
            [
                [lon - d, lat - d],
                [lon + d, lat - d],
                [lon + d, lat + d],
                [lon - d, lat + d],
                [lon - d, lat - d],
            ]
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": polygon},
                "properties": {
                    "naziv": r.naziv,
                    "ukupno": uk,
                    "slobodni": r.slobodni or 0,
                    "postotak_zauzetosti": postotak,
                    "lat": lat,
                    "lon": lon,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
