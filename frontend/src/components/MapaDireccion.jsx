import { useEffect } from "react"
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet"
import L from "leaflet"
import "leaflet/dist/leaflet.css"

const MARCADOR = L.divIcon({
  className: "",
  html: `<svg width="28" height="36" viewBox="0 0 24 31" aria-hidden="true"><path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 19 12 19s12-10 12-19C24 5.4 18.6 0 12 0z" fill="#9D0208"/><circle cx="12" cy="12" r="4.5" fill="#fff"/></svg>`,
  iconSize: [28, 36],
  iconAnchor: [14, 36],
})

function Clics({ onSeleccionar }) {
  useMapEvents({
    click: (e) => onSeleccionar([e.latlng.lat, e.latlng.lng]),
  })
  return null
}

function Recentrar({ posicion }) {
  const map = useMap()
  useEffect(() => {
    map.setView(posicion)
  }, [map, posicion])
  return null
}

export default function MapaDireccion({ posicion, onSeleccionar }) {
  return (
    <div className="relative isolate z-0 h-[230px] w-full overflow-hidden rounded-2xl">
      <MapContainer center={posicion} zoom={15} scrollWheelZoom={false} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={posicion} icon={MARCADOR} />
        <Clics onSeleccionar={onSeleccionar} />
        <Recentrar posicion={posicion} />
      </MapContainer>
    </div>
  )
}