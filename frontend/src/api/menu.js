import api from "./cliente"

// `negocio` filtra el menú público; el personal siempre recibe el de su negocio.
export async function listarCategorias(negocio) {
  const { data } = await api.get("/menu/categorias/", {
    params: negocio ? { negocio } : undefined,
  })
  return data
}

export async function crearCategoria(datos) {
  const { data } = await api.post("/menu/categorias/", datos)
  return data
}

export async function actualizarCategoria(id, datos) {
  const { data } = await api.patch(`/menu/categorias/${id}/`, datos)
  return data
}

export async function listarProductos(incluirInactivos = false) {
  const { data } = await api.get("/menu/productos/", {
    params: incluirInactivos ? { incluir_inactivos: "true" } : undefined,
  })
  return data
}

export async function obtenerProducto(id) {
  const { data } = await api.get(`/menu/productos/${id}/`)
  return data
}

export async function crearProducto(datos) {
  const { data } = await api.post("/menu/productos/", datos)
  return data
}

export async function reemplazarProducto(id, datos) {
  const { data } = await api.put(`/menu/productos/${id}/`, datos)
  return data
}

export async function cambiarDisponibilidadProducto(id, disponible) {
  const { data } = await api.patch(`/menu/productos/${id}/`, { disponible })
  return data
}

export async function desactivarProducto(id) {
  const { data } = await api.delete(`/menu/productos/${id}/`)
  return data
}

export async function configurarGrupoOpciones(productoId, grupo) {
  const { data } = await api.post(`/menu/productos/${productoId}/opciones/`, grupo)
  return data
}

export async function obtenerCatalogoSede(sedeId) {
  const { data } = await api.get(`/menu/sedes/${sedeId}/catalogo/`)
  return data
}
