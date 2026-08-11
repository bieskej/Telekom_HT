# Mapa općina – choropleth na dashboardu

Dashboard pokazuje sve općine BiH koje imaju HT Eronet MSISDN-e kao
choropleth mapu (boja punjenja prema postotku zauzetosti).

## Izvor koordinata

Statički rječnik `KOORDINATE` u `backend/scripts/seed_opcine_geo.py`
sadrži lat/lon (WGS84) za **39 općina** HT Eronet mreže. Vrijednosti su
prikupljene iz:

- Wikipedia infobox-a za gradove (Mostar, Sarajevo, Tuzla, Banja Luka, …).
- OpenStreetMap Nominatim za manja mjesta (Crnići, Hodovo, Domaljevac, Ravno).

Idempotentna `UPDATE` skripta (`python -m scripts.seed_opcine_geo`)
puni kolone `opcine.lat` i `opcine.lon` (dodane Alembic migracijom
`002_opcine_lat_lon`).

## Endpoint `GET /opcine/geojson`

```http
GET /opcine/geojson
Authorization: Bearer <token>
```

Vraća GeoJSON `FeatureCollection`. Svaka `Feature` predstavlja jednu
općinu s pojednostavljenom **bbox geometrijom** (kvadrat ±0.04° ≈ 4.4 km
oko centroida).

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon-d, lat-d], [lon+d, lat-d], [lon+d, lat+d], [lon-d, lat+d], [lon-d, lat-d]]]
      },
      "properties": {
        "naziv": "Mostar",
        "ukupno": 77016,
        "slobodni": 77016,
        "postotak_zauzetosti": 0.0,
        "lat": 43.3438,
        "lon": 17.8078
      }
    }
  ]
}
```

## Frontend (`OpcinaMap.tsx`)

- Učitava `/opcine/geojson` i prikazuje `<GeoJSON>` layer preko OpenStreetMap-a.
- **Boja punjenja**: zelena < 50 %, žuta 50 – 90 %, crvena > 90 %.
- **Popup** na klik: naziv, ukupno, slobodno, zauzetost.
- **Hover**: tamnija obrub + crveniji fill.
- **Klik**: navigira na `/brojevi?opcina_naziv=<naziv>`.
- **Legenda**: fixed u donjem desnom kutu mape.
- **FitBounds**: mapa se automatski centrira na bbox svih učitanih općina.

## Statistika `po_opcini` – dodatne kolone

Endpoint `GET /statistike` u objektu `po_opcini` sada vraća i `lat`/`lon`
ako su poznate.

```json
{
  "naziv": "Mostar",
  "postotak_zauzetosti": 0.0,
  "slobodni": 77016,
  "ukupno": 77016,
  "lat": 43.3438,
  "lon": 17.8078
}
```

## Zamjena bbox-a pravim granicama (TODO)

Trenutna bbox geometrija je pojednostavljena (kvadrat). Za pravi
choropleth s realnim granicama:

1. Preuzeti **GADM BIH level 3** ili **OSM Boundaries** za općine BiH
   (GeoJSON ili Shapefile).
2. Spremiti u `backend/data/opcine_bih.geojson`.
3. U endpointu `GET /opcine/geojson` zamijeniti generiranje polygona
   čitanjem geometrije iz tog fajla (match po nazivu općine).
4. Cache datoteku u memoriju (učitaj jednom pri startu app-a).

Komentar `# TODO` postavljen je u `backend/app/routers/opcine.py` iznad
`GEOJSON_BBOX_DELTA`.

## Migracija

```bash
cd backend
alembic upgrade head      # primjenjuje 002_opcine_lat_lon
python -m scripts.seed_opcine_geo
```

## Testovi

```
backend/tests/test_opcine_geojson.py   – 6 testova (struktura, auth, kompletnost)
backend/tests/test_statistike_sjedista.py – 7 testova (po_opcini lat/lon, po_sjedistima)
backend/tests/test_seed_opcine_geo.py  – 4 testa (idempotentnost, geografski raspon)
```

Pokretanje: `cd backend && python -m pytest --ignore=tests/test_email_service.py`.
