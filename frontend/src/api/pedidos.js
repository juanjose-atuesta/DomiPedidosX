import api from "./cliente"

// filtros: { sede, estado, fecha }. `estado` admite varios valores separados por coma.
export async function listarPedidos(filtros = {}) {
  const { data } = await api.get("/pedidos/", { params: filtros })
  return data
}

// Obtener los detalles de un pedido específico.
export async function obtenerPedido(id) {
  const { data } = await api.get(`/pedidos/${id}/`)
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

// Desglose (subtotal, descuento, domicilio, total) y problemas antes de confirmar.
export async function cotizarPedido(datos) {
  const { data } = await api.post("/pedidos/cotizar/", datos)
  return data
}

export async function cancelarPedido(id, motivo = "") {
  const { data } = await api.post(`/pedidos/${id}/cancelar/`, { motivo })
  return data
}

// El operador rechaza un pedido entrante; el motivo (mín. 10 caracteres) lo ve el cliente.
export async function rechazarPedido(id, motivo) {
  const { data } = await api.post(`/pedidos/${id}/rechazar/`, { motivo })
  return data
}

export async function enviarUbicacionPedido(id, latitud, longitud) {
  await api.post(`/pedidos/${id}/ubicacion/`, { latitud, longitud })
}
