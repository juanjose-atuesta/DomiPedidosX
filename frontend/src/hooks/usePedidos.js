import { useCallback, useEffect, useState } from "react"
import { actualizarEstadoPedido, listarPedidos } from "../api/pedidos"
import { mensajeDeError } from "../utils/errores"

const INTERVALO_ACTUALIZACION_MS = 30000

// Lista pedidos con los filtros dados, la refresca periódicamente y permite avanzar su estado.
export function usePedidos({ sede, estado, fecha, intervalo = INTERVALO_ACTUALIZACION_MS }) {
  const clave = `${sede}|${estado}|${fecha}`
  const [pedidos, setPedidos] = useState([])
  const [cargadoDe, setCargadoDe] = useState(null)
  const [error, setError] = useState("")
  const [procesandoId, setProcesandoId] = useState(null)
  // Al cambiar fuerza una consulta inmediata (p. ej. al llegar una alerta de cancelación).
  const [recargas, setRecargas] = useState(0)

  useEffect(() => {
    let vigente = true
    const filtros = {
      ...(sede ? { sede } : {}),
      ...(estado ? { estado } : {}),
      ...(fecha ? { fecha } : {}),
    }

    const cargar = () =>
      listarPedidos(filtros)
        .then((datos) => {
          if (!vigente) return
          setPedidos(datos)
          setError("")
        })
        .catch((err) => {
          if (vigente) setError(mensajeDeError(err, "No se pudieron cargar los pedidos."))
        })
        .finally(() => {
          if (vigente) setCargadoDe(clave)
        })

    cargar()
    const temporizador = setInterval(cargar, intervalo)

    return () => {
      vigente = false
      clearInterval(temporizador)
    }
  }, [clave, sede, estado, fecha, intervalo, recargas])

  const avanzar = async (pedido, nuevoEstado) => {
    setProcesandoId(pedido.id)
    setError("")

    try {
      const actualizado = await actualizarEstadoPedido(pedido.id, nuevoEstado)
      setPedidos((actuales) =>
        actuales.map((p) => (p.id === actualizado.id ? actualizado : p)),
      )
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo actualizar el pedido."))
    } finally {
      setProcesandoId(null)
    }
  }

  // Para acciones hechas fuera del hook (p. ej. la cancelación del cliente).
  const reemplazar = (actualizado) =>
    setPedidos((actuales) => actuales.map((p) => (p.id === actualizado.id ? actualizado : p)))

  const recargar = useCallback(() => setRecargas((n) => n + 1), [])

  return {
    pedidos,
    cargando: cargadoDe !== clave,
    error,
    procesandoId,
    avanzar,
    reemplazar,
    recargar,
  }
}
