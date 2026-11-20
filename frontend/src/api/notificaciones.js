import api from "./cliente"

export async function obtenerConfiguracionCorreos() {
  const { data } = await api.get("/notificaciones/configuracion-correos/")
  return data
}

export async function actualizarConfiguracionCorreos(datos) {
  const { data } = await api.patch("/notificaciones/configuracion-correos/", datos)
  return data
}
