import api from "./cliente"

export async function obtenerConfiguracionCorreos() {
  const { data } = await api.get("/notificaciones/configuracion-correos/")
  return data
}

export async function actualizarConfiguracionCorreos(datos) {
  const { data } = await api.patch("/notificaciones/configuracion-correos/", datos)
  return data
}

// Alertas del panel del personal (p. ej. pedidos cancelados por el cliente).
// filtros: { sede, leida, tipo }. Responde { no_leidas, resultados }.
export async function listarNotificaciones(filtros = {}) {
  const { data } = await api.get("/notificaciones/", { params: filtros })
  return data
}

export async function marcarNotificacionLeida(id, leida = true) {
  const { data } = await api.patch(`/notificaciones/${id}/`, { leida })
  return data
}

export async function marcarTodasLeidas() {
  const { data } = await api.post("/notificaciones/marcar-leidas/")
  return data
}
