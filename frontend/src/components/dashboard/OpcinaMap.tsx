import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import type { Layer, PathOptions } from 'leaflet'
import type { Feature } from 'geojson'
import 'leaflet/dist/leaflet.css'

import { api } from '@/lib/api'
import { bojaZaZauzetost, ZAUZETOST_LEGENDA } from '@/lib/statusUi'
import type { OpcinaGeoFeature, OpcineGeoJson } from '@/types/api'

const TOP_N = 15

function FitBounds({ data }: { data: OpcineGeoJson | null }) {
  const map = useMap()
  useEffect(() => {
    if (!data?.features?.length) return
    const lats = data.features.map((f) => f.properties.lat)
    const lons = data.features.map((f) => f.properties.lon)
    const minLat = Math.min(...lats)
    const maxLat = Math.max(...lats)
    const minLon = Math.min(...lons)
    const maxLon = Math.max(...lons)
    map.fitBounds(
      [
        [minLat - 0.2, minLon - 0.2],
        [maxLat + 0.2, maxLon + 0.2],
      ],
      { padding: [20, 20] },
    )
  }, [data, map])
  return null
}

function Legenda() {
  return (
    <div className="absolute bottom-3 right-3 z-[1000] rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-md backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
      <p className="mb-1.5 font-semibold text-slate-700 dark:text-slate-200">Zauzetost</p>
      {ZAUZETOST_LEGENDA.map((item) => (
        <div key={item.label} className="mt-1 flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 rounded"
            style={{ backgroundColor: item.boja }}
            aria-hidden
          />
          <span className="text-slate-600 dark:text-slate-400">{item.label}</span>
        </div>
      ))}
    </div>
  )
}

function OpcinaTablica({ features }: { features: OpcinaGeoFeature[] }) {
  const navigate = useNavigate()
  const redovi = useMemo(
    () =>
      [...features]
        .sort((a, b) => b.properties.postotak_zauzetosti - a.properties.postotak_zauzetosti)
        .slice(0, TOP_N),
    [features],
  )

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-800">
      <table className="w-full min-w-[480px] text-left text-sm">
        <caption className="sr-only">
          Tablica zauzetosti po općinama, sortirano silazno. Prikazano prvih {TOP_N} općina.
        </caption>
        <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase text-slate-500 dark:border-slate-800 dark:bg-slate-800/50">
          <tr>
            <th scope="col" className="px-4 py-3">
              Općina
            </th>
            <th scope="col" className="px-4 py-3 text-right">
              Zauzetost
            </th>
            <th scope="col" className="px-4 py-3 text-right">
              Ukupno
            </th>
            <th scope="col" className="px-4 py-3 text-right">
              Slobodno
            </th>
          </tr>
        </thead>
        <tbody>
          {redovi.map((f) => {
            const p = f.properties
            const boja = bojaZaZauzetost(p.postotak_zauzetosti)
            return (
              <tr
                key={p.naziv}
                className="border-b border-slate-50 last:border-0 dark:border-slate-800"
              >
                <td className="px-4 py-2.5">
                  <button
                    type="button"
                    className="font-medium text-[#0054A6] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00A3E0]"
                    onClick={() =>
                      navigate(`/brojevi?opcina_naziv=${encodeURIComponent(p.naziv)}`)
                    }
                  >
                    {p.naziv}
                  </button>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: boja }}
                      aria-hidden
                    />
                    <span>{p.postotak_zauzetosti}%</span>
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {p.ukupno.toLocaleString('hr-HR')}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums text-emerald-700 dark:text-emerald-400">
                  {p.slobodni.toLocaleString('hr-HR')}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500 dark:border-slate-800">
        Prikaz top {TOP_N} općina po zauzetosti. Boja na mapi i u tablici ista legenda.
      </p>
    </div>
  )
}

export function OpcinaMap() {
  const [data, setData] = useState<OpcineGeoJson | null>(null)
  const [loading, setLoading] = useState(true)
  const [greska, setGreska] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api
      .opcineGeoJson()
      .then((g) => setData(g))
      .catch((e) => setGreska(e instanceof Error ? e.message : 'Greška'))
      .finally(() => setLoading(false))
  }, [])

  const style = (feature?: Feature): PathOptions => {
    const f = feature as OpcinaGeoFeature | undefined
    const post = f?.properties?.postotak_zauzetosti ?? 0
    const boja = bojaZaZauzetost(post)
    return {
      color: '#1e293b',
      weight: 1,
      fillColor: boja,
      fillOpacity: 0.65,
    }
  }

  const onEachFeature = (feature: Feature, layer: Layer) => {
    const props = (feature as OpcinaGeoFeature).properties
    layer.bindTooltip(props.naziv, {
      sticky: true,
      direction: 'top',
      opacity: 0.95,
      className: 'opcina-map-tooltip',
    })
    layer.bindPopup(
      `<div style="min-width:160px">
        <strong>${props.naziv}</strong><br/>
        Ukupno: <b>${props.ukupno.toLocaleString('hr-HR')}</b><br/>
        Slobodno: <b style="color:#16a34a">${props.slobodni.toLocaleString('hr-HR')}</b><br/>
        Zauzetost: <b>${props.postotak_zauzetosti}%</b>
      </div>`,
    )
    layer.on({
      mouseover: (e) => {
        const target = e.target as L.Path
        target.setStyle({ weight: 3, color: '#0054A6', fillOpacity: 0.85 })
      },
      mouseout: (e) => {
        const target = e.target as L.Path
        target.setStyle(style(feature))
      },
      click: () => {
        navigate(`/brojevi?opcina_naziv=${encodeURIComponent(props.naziv)}`)
      },
    })
  }

  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-sm text-slate-500">
        Učitavanje mape…
      </div>
    )
  }

  if (greska) {
    return (
      <div className="flex h-96 w-full items-center justify-center rounded-xl border border-red-200 bg-red-50 text-sm text-red-700">
        Greška pri učitavanju mape: {greska}
      </div>
    )
  }

  const features = (data?.features ?? []) as OpcinaGeoFeature[]

  return (
    <div className="space-y-4">
      <div className="print-hide-map relative h-96 w-full overflow-hidden rounded-xl border border-slate-100 shadow-[var(--shadow-card)] dark:border-slate-700">
        <MapContainer
          center={[44.0, 17.7]}
          zoom={7}
          className="h-full w-full"
          scrollWheelZoom={false}
          aria-label="Interaktivna mapa zauzetosti po općinama"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {data && (
            <>
              <GeoJSON data={data} style={style} onEachFeature={onEachFeature} />
              <FitBounds data={data} />
            </>
          )}
        </MapContainer>
        <Legenda />
      </div>
      {features.length > 0 && <OpcinaTablica features={features} />}
    </div>
  )
}
