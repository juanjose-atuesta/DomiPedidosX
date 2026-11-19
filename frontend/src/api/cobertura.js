import api from "./cliente"

export async function listarZonas(sedeId) {
  const { data } = await api.get(`/cobertura/sedes/${sedeId}/zonas/`)
  return data
}

export async function crearZona(sedeId, datos) {
  const { data } = await api.post(`/cobertura/sedes/${sedeId}/zonas/`, datos)
  return data
}

export async function actualizarZona(id, datos) {
  const { data } = await api.patch(`/cobertura/zonas/${id}/`, datos)
  return data
}

export async function desactivarZona(id) {
  const { data } = await api.delete(`/cobertura/zonas/${id}/`)
  return data
}

// Público: qué sedes llegan a un punto. Devuelve { cubierta, zonas }.
export async function verificarCobertura([lat, lng], sedeId) {
  const { data } = await api.get("/cobertura/verificar/", {
    params: { lat: lat.toFixed(6), lng: lng.toFixed(6), ...(sedeId ? { sede: sedeId } : {}) },
  })
  return data
}
