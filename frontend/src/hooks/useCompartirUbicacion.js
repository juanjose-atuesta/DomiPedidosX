import { useEffect } from "react"
import { enviarUbicacionPedido } from "../api/pedidos"

const INTERVALO_UBICACION_MS = 30000

// HU-7.7: mientras `activo` sea true (pedido en camino), envía la ubicación cada 30 s.
export function useCompartirUbicacion(pedidoId, activo) {
  useEffect(() => {
    if (!activo || !navigator.geolocation) return undefined

    const enviar = () =>
      navigator.geolocation.getCurrentPosition(
        ({ coords }) =>
          enviarUbicacionPedido(pedidoId, coords.latitude, coords.longitude).catch((error) =>
            console.warn("No se pudo enviar la ubicación:", error),
          ),
        (error) => console.warn("Ubicación no disponible:", error.code, error.message),
        { timeout: 20000, maximumAge: 15000 },
      )

    enviar()
    const temporizador = setInterval(enviar, INTERVALO_UBICACION_MS)
    return () => clearInterval(temporizador)
  }, [pedidoId, activo])
}