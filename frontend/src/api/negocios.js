import api from "./cliente"

// Porcentaje de alerta de capacidad del negocio (aplica a todas sus sedes).
export async function obtenerConfiguracionCapacidad() {
  const { data } = await api.get("/negocios/configuracion-capacidad/")
  return data
}

export async function actualizarConfiguracionCapacidad(datos) {
  const { data } = await api.patch("/negocios/configuracion-capacidad/", datos)
  return data
}
