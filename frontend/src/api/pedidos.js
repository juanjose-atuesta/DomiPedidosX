import api from "./cliente"

// filtros: { sede, estado, fecha }. `estado` admite varios valores separados por coma.
export async function listarPedidos(filtros = {}) {
  const { data } = await api.get("/pedidos/", { params: filtros })
  return data
}

export async function actualizarEstadoPedido(id, estado, comentario = "") {
  const { data } = await api.patch(`/pedidos/${id}/estado/`, { estado, comentario })
  return data
}

export async function crearPedido(datos) {
  const { data } = await api.post("/pedidos/", datos)
  return data
}
