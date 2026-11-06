export const CANTIDAD_MINIMA = 1
export const CANTIDAD_MAXIMA = 10

export const METODOS_PAGO = [
  { valor: "efectivo", etiqueta: "Efectivo" },
  { valor: "tarjeta", etiqueta: "Tarjeta" },
  { valor: "transferencia", etiqueta: "Transferencia" },
]

export function limitarCantidad(cantidad) {
  return Math.min(CANTIDAD_MAXIMA, Math.max(CANTIDAD_MINIMA, cantidad))
}

// Dos líneas son la misma si coinciden el producto, las opciones y las notas.
export function construirLinea(producto, opciones, cantidad, notas = "") {
  const notasLimpias = notas.trim()
  const idsOpciones = opciones.map((o) => o.id).sort()
  return {
    clave: [producto.id, ...idsOpciones, notasLimpias].join("|"),
    productoId: producto.id,
    nombre: producto.nombre,
    precio: producto.precio,
    opciones,
    notas: notasLimpias,
    cantidad: limitarCantidad(cantidad),
  }
}

export function agregarLinea(lineas, nueva) {
  if (!lineas.some((l) => l.clave === nueva.clave)) return [...lineas, nueva]
  return lineas.map((l) =>
    l.clave === nueva.clave
      ? { ...l, cantidad: limitarCantidad(l.cantidad + nueva.cantidad) }
      : l,
  )
}

export function cambiarCantidadLinea(lineas, clave, cantidad) {
  return lineas.map((l) =>
    l.clave === clave ? { ...l, cantidad: limitarCantidad(cantidad) } : l,
  )
}

export function quitarLinea(lineas, clave) {
  return lineas.filter((l) => l.clave !== clave)
}

export function subtotalLinea(linea) {
  const extras = linea.opciones.reduce((suma, o) => suma + o.extra, 0)
  return (linea.precio + extras) * linea.cantidad
}

export function subtotalLineas(lineas) {
  return lineas.reduce((suma, l) => suma + subtotalLinea(l), 0)
}

export function detallesDePedido(lineas) {
  return lineas.map((l) => ({
    producto_id: l.productoId,
    cantidad: l.cantidad,
    notas_producto: l.notas,
    opciones: l.opciones.map((o) => o.id),
  }))
}

export function datosDeEntrega(direccion) {
  return {
    direccion_entrega: [direccion.direccion_texto, direccion.detalles]
      .filter(Boolean)
      .join(" - "),
    entrega_lat: direccion.latitud,
    entrega_lng: direccion.longitud,
  }
}

// La principal primero, para usarla como dirección por defecto.
export function direccionPorDefecto(direcciones) {
  return direcciones.find((d) => d.es_principal) ?? direcciones[0] ?? null
}
