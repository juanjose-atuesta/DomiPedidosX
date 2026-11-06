import api from "./cliente"

export async function listarDirecciones() {
  const { data } = await api.get("/usuarios/direcciones/")
  return data
}

export async function crearDireccion(datos) {
  const { data } = await api.post("/usuarios/direcciones/", datos)
  return data
}

export async function actualizarDireccion(id, datos) {
  const { data } = await api.patch(`/usuarios/direcciones/${id}/`, datos)
  return data
}

export async function eliminarDireccion(id) {
  const { data } = await api.delete(`/usuarios/direcciones/${id}/`)
  return data
}
