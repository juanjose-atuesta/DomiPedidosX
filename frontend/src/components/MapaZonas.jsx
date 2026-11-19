import { Circle, CircleMarker, MapContainer, Polygon, TileLayer, useMapEvents } from "react-leaflet"
import "leaflet/dist/leaflet.css"

const COLOR_ZONA = "#9D0208"
const COLOR_EDICION = "#F48C06"

function Clics({ onClic }) {
  useMapEvents({
    click: (e) => onClic?.([e.latlng.lat, e.latlng.lng]),
  })
  return null
}

function Figura({ zona, color, discontinua = false }) {
  const estilo = { color, weight: 2, fillOpacity: 0.12, dashArray: discontinua ? "6 6" : undefined }
  if (zona.tipo === "radio" && zona.centro && zona.radioKm > 0) {
    return <Circle center={zona.centro} radius={zona.radioKm * 1000} pathOptions={estilo} />
  }
  if (zona.tipo === "poligono" && zona.puntos.length >= 2) {
    return <Polygon positions={zona.puntos} pathOptions={estilo} />
  }
  return null
}

// Muestra las zonas guardadas y la que se está editando. Cada clic en el mapa
// llama a `onClic` (centro del radio o un vértice nuevo del polígono).
export default function MapaZonas({ centro, zonas, edicion, onClic }) {
  return (
    <div className="relative isolate z-0 h-[420px] w-full overflow-hidden rounded-xl border border-borde">
      <MapContainer center={centro} zoom={13} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zonas.map((zona) => (
          <Figura key={zona.id} zona={zona} color={COLOR_ZONA} />
        ))}
        {edicion && <Figura zona={edicion} color={COLOR_EDICION} discontinua />}
        {edicion?.tipo === "poligono" &&
          edicion.puntos.map((punto, i) => (
            <CircleMarker
              key={`${punto[0]}-${punto[1]}-${i}`}
              center={punto}
              radius={5}
              pathOptions={{ color: COLOR_EDICION, fillOpacity: 1 }}
            />
          ))}
        {edicion?.tipo === "radio" && edicion.centro && (
          <CircleMarker center={edicion.centro} radius={5} pathOptions={{ color: COLOR_EDICION, fillOpacity: 1 }} />
        )}
        <Clics onClic={onClic} />
      </MapContainer>
    </div>
  )
}
