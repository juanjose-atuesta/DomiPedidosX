import { useEffect, useRef, useState } from "react"
import { Campana } from "./Iconos"
import {
  listarNotificaciones,
  marcarNotificacionLeida,
  marcarTodasLeidas,
} from "../api/notificaciones"
import { formatearFechaHora } from "../utils/formato"

const INTERVALO_MS = 5000

// Campana del panel del personal: consulta las alertas cada 5 s (HU-7.5).
// `onNuevas` se llama cuando llegan alertas que no se habían visto, para que la
// vista recargue sus pedidos (un cancelado sale de entrantes y del tablero).
export default function CampanaNotificaciones({ onNuevas, intervalo = INTERVALO_MS }) {
  const [datos, setDatos] = useState({ no_leidas: 0, resultados: [] })
  const [abierta, setAbierta] = useState(false)
  const vistas = useRef(null)
  const alNotificar = useRef(onNuevas)

  useEffect(() => {
    alNotificar.current = onNuevas
  }, [onNuevas])

  useEffect(() => {
    let vigente = true
    const cargar = () =>
      listarNotificaciones()
        .then((respuesta) => {
          if (!vigente) return
          const ids = new Set(respuesta.resultados.map((n) => n.id))
          const hayNuevas =
            vistas.current !== null && [...ids].some((id) => !vistas.current.has(id))
          vistas.current = ids
          setDatos(respuesta)
          if (hayNuevas) alNotificar.current?.()
        })
        .catch(() => {
          // Un fallo puntual no debe interrumpir el panel; se reintenta en 5 s.
        })

    cargar()
    const temporizador = setInterval(cargar, intervalo)
    return () => {
      vigente = false
      clearInterval(temporizador)
    }
  }, [intervalo])

  const marcar = async (notificacion) => {
    if (notificacion.leida) return
    try {
      await marcarNotificacionLeida(notificacion.id)
      setDatos((actual) => ({
        no_leidas: Math.max(0, actual.no_leidas - 1),
        resultados: actual.resultados.map((n) =>
          n.id === notificacion.id ? { ...n, leida: true } : n,
        ),
      }))
    } catch {
      // Se reintenta en el siguiente clic.
    }
  }

  const marcarTodas = async () => {
    try {
      await marcarTodasLeidas()
      setDatos((actual) => ({
        no_leidas: 0,
        resultados: actual.resultados.map((n) => ({ ...n, leida: true })),
      }))
    } catch {
      // Se reintenta en el siguiente clic.
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setAbierta((a) => !a)}
        aria-label={`Notificaciones: ${datos.no_leidas} sin leer`}
        aria-expanded={abierta}
        className="relative flex h-11 w-11 items-center justify-center rounded-full border border-borde bg-white text-texto hover:bg-fondo"
      >
        <Campana />
        {datos.no_leidas > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-acento px-1 text-xs font-semibold text-white">
            {datos.no_leidas > 99 ? "99+" : datos.no_leidas}
          </span>
        )}
      </button>

      {abierta && (
        <div className="absolute right-0 z-20 mt-2 flex max-h-[420px] w-[360px] max-w-[90vw] flex-col overflow-hidden rounded-xl border border-borde bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-borde px-4 py-3">
            <p className="font-semibold text-texto">Notificaciones</p>
            {datos.no_leidas > 0 && (
              <button
                type="button"
                onClick={marcarTodas}
                className="text-sm font-semibold text-acento hover:underline"
              >
                Marcar todas como leídas
              </button>
            )}
          </div>
          <ul className="overflow-y-auto">
            {datos.resultados.length === 0 && (
              <li className="px-4 py-6 text-center text-sm text-texto-sec">
                No hay notificaciones.
              </li>
            )}
            {datos.resultados.map((n) => (
              <li key={n.id} className="border-b border-borde last:border-0">
                <button
                  type="button"
                  onClick={() => marcar(n)}
                  className={`flex w-full flex-col gap-1 px-4 py-3 text-left ${
                    n.leida ? "bg-white" : "bg-fondo-aviso"
                  }`}
                >
                  <span className="text-sm font-semibold text-texto">{n.asunto}</span>
                  <span className="text-sm text-texto-sec">{n.mensaje}</span>
                  <span className="text-xs text-texto-sec">
                    {formatearFechaHora(n.creado_en)}
                    {!n.leida && " · Toca para marcar como leída"}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
