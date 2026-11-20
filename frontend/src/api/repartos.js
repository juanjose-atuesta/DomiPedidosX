import api from "./cliente"

// { sede_id, asignacion_automatica_repartidor, repartidores: [{ id, nombre, estado, pedidos_hoy, ... }] }
export async function listarRepartidores(sedeId) {
  const { data } = await api.get(`/repartos/sedes/${sedeId}/repartidores/`)
  return data
}

export async function asignarRepartidor(pedidoId, repartidorId) {
  const { data } = await api.post(`/repartos/pedidos/${pedidoId}/asignar/`, {
    repartidor_id: repartidorId,
  })
  return data
}

export async function configurarAsignacionAutomatica(sedeId, activa) {
  const { data } = await api.patch(`/repartos/sedes/${sedeId}/configuracion/`, {
    asignacion_automatica_repartidor: activa,
  })
  return data
}
