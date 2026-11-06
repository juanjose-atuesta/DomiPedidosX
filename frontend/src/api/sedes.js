import api from "./cliente"

export async function listarSedes(incluirInactivas = false) {
  const { data } = await api.get("/sedes/", {
    params: incluirInactivas ? { incluir_inactivas: "true" } : undefined,
  })
  return data
}

export async function obtenerSede(id) {
  const { data } = await api.get(`/sedes/${id}/`)
  return data
}

export async function crearSede(datos) {
  const { data } = await api.post("/sedes/", datos)
  return data
}

export async function actualizarSede(id, datos) {
  const { data } = await api.patch(`/sedes/${id}/`, datos)
  return data
}

export async function reemplazarSede(id, datos) {
  const { data } = await api.put(`/sedes/${id}/`, datos)
  return data
}

export async function desactivarSede(id) {
  const { data } = await api.delete(`/sedes/${id}/`)
  return data
}

export async function reactivarSede(id) {
  const { data } = await api.post(`/sedes/${id}/reactivar/`)
  return data
}
