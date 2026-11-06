import api from "./cliente"

export async function listarInventario(sedeId) {
  const { data } = await api.get(`/inventario/sedes/${sedeId}/`)
  return data
}

// Crea o actualiza la fila del producto en la sede.
export async function guardarInventario(sedeId, datos) {
  const { data } = await api.post(`/inventario/sedes/${sedeId}/`, datos)
  return data
}
