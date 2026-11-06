// Mismo criterio que el backend guarda en el pedido, para que cliente y cocina lean lo mismo.
function nombreOpcion(opcion, tipo) {
  if (tipo !== "excluible" || /^sin\s/i.test(opcion.nombre)) return opcion.nombre
  return `Sin ${opcion.nombre.toLowerCase()}`
}

// Adapta un producto del catálogo: opciones activas por tipo y precios numéricos.
export function normalizarProducto(producto) {
  const opciones = (tipo) =>
    producto.grupos_opcion
      .filter((grupo) => grupo.tipo === tipo)
      .flatMap((grupo) => grupo.opciones)
      .filter((opcion) => opcion.activa)
      .map((opcion) => ({
        id: opcion.id,
        nombre: nombreOpcion(opcion, tipo),
        extra: Number(opcion.precio_adicional),
      }))

  return {
    id: producto.id,
    nombre: producto.nombre,
    precio: Number(producto.precio_base),
    tiempo: producto.tiempo_preparacion_min,
    descripcion: producto.descripcion,
    imagen: producto.imagen_url,
    agotado: producto.agotado,
    tamanos: opciones("tamano"),
    adiciones: opciones("adicion"),
    excluibles: opciones("excluible"),
  }
}
