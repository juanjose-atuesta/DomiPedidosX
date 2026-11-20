import { useEffect, useState } from "react"
import { useAuth } from "./auth-context"
import { CarritoContext } from "./carrito-context"
import { agregarLinea, cambiarCantidadLinea, quitarLinea } from "../utils/carrito"

function leerCarritos(clave) {
  try {
    const guardado = JSON.parse(localStorage.getItem(clave))
    return guardado && typeof guardado === "object" ? guardado : {}
  } catch {
    return {}
  }
}

function guardarCarritos(clave, carritos) {
  try {
    localStorage.setItem(clave, JSON.stringify(carritos))
  } catch {
    // Sin almacenamiento el carrito solo dura mientras la página siga abierta.
  }
}

// Las líneas se agrupan por sede: un pedido solo puede prepararse en una.
function CarritoDeUsuario({ clave, children }) {
  const [carritos, setCarritos] = useState(() => (clave ? leerCarritos(clave) : {}))

  useEffect(() => {
    if (clave) guardarCarritos(clave, carritos)
  }, [clave, carritos])

  const actualizar = (sedeId, transformar) =>
    setCarritos((actuales) => {
      const { [sedeId]: lineas = [], ...resto } = actuales
      const nuevas = transformar(lineas)
      return nuevas.length > 0 ? { ...resto, [sedeId]: nuevas } : resto
    })

  const valor = {
    carritos,
    agregar: (sedeId, linea) => actualizar(sedeId, (ls) => agregarLinea(ls, linea)),
    cambiarCantidad: (sedeId, clave, cantidad) =>
      actualizar(sedeId, (ls) => cambiarCantidadLinea(ls, clave, cantidad)),
    quitar: (sedeId, clave) => actualizar(sedeId, (ls) => quitarLinea(ls, clave)),
    vaciar: (sedeId) => actualizar(sedeId, () => []),
  }

  return <CarritoContext.Provider value={valor}>{children}</CarritoContext.Provider>
}

export function CarritoProvider({ children }) {
  const { usuario } = useAuth()
  // Cada usuario tiene su carrito, aunque compartan el navegador.
  const clave = usuario ? `domipedidos.carrito.${usuario.id}` : null

  return (
    <CarritoDeUsuario key={clave ?? "sin-sesion"} clave={clave}>
      {children}
    </CarritoDeUsuario>
  )
}
