import api from "./cliente"

export async function listarPromocionesGestion() {
  const { data } = await api.get("/promociones/", {
    params: { incluir_inactivas: "true" },
  })
  return data
}

export async function obtenerPromocion(id) {
  const { data } = await api.get(`/promociones/${id}/`)
  return data
}

export async function crearPromocion(datos) {
  const { data } = await api.post("/promociones/", datos)
  return data
}

export async function actualizarPromocion(id, datos) {
  const { data } = await api.patch(`/promociones/${id}/`, datos)
  return data
}

export async function desactivarPromocion(id) {
  const { data } = await api.delete(`/promociones/${id}/`)
  return data
}
