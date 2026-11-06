import api from "./cliente"

export async function registrarCliente(datos) {
  const { data } = await api.post("/usuarios/registro/", datos)
  return data
}

export async function iniciarSesion({ email, password }) {
  const { data } = await api.post("/auth/login/", { email, password })
  return data
}

export async function obtenerPerfil() {
  const { data } = await api.get("/usuarios/me/")
  return data
}

export async function actualizarPerfil(datos) {
  const { data } = await api.patch("/usuarios/me/", datos)
  return data
}
