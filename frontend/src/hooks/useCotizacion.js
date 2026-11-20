import { useEffect, useState } from "react"
import { cotizarPedido } from "../api/pedidos"
import { mensajeDeError } from "../utils/errores"

const ESPERA_MS = 350

// Pide al backend el desglose del pedido (subtotal, descuento, domicilio, total)
// cada vez que cambian sus datos. `datos` en null = aún no hay nada que cotizar.
export function useCotizacion(datos) {
  const clave = datos ? JSON.stringify(datos) : ""
  const [resultado, setResultado] = useState({ clave: "", cotizacion: null, error: "" })

  useEffect(() => {
    if (!clave) return undefined
    let vigente = true

    const temporizador = setTimeout(() => {
      cotizarPedido(JSON.parse(clave))
        .then((cotizacion) => {
          if (vigente) setResultado({ clave, cotizacion, error: "" })
        })
        .catch((err) => {
          if (vigente) {
            setResultado({
              clave,
              cotizacion: null,
              error: mensajeDeError(err, "No se pudo calcular el total del pedido."),
            })
          }
        })
    }, ESPERA_MS)

    return () => {
      vigente = false
      clearTimeout(temporizador)
    }
  }, [clave])

  const alDia = Boolean(clave) && resultado.clave === clave
  return {
    cotizacion: alDia ? resultado.cotizacion : null,
    error: alDia ? resultado.error : "",
    cargando: Boolean(clave) && !alDia,
  }
}
