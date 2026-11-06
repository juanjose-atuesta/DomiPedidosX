import api from "./cliente"

export async function listarUsuarios() {
  const { data } = await api.get("/usuarios/usuarios/")
  return data
}

export async function crearPersonal(datos) {
  const { data } = await api.post("/usuarios/personal/", datos)
  return data
}

export async function cambiarRolUsuario(id, nuevoRol) {
  const { data } = await api.patch(`/usuarios/usuarios/${id}/cambiar-rol/`, {
    rol: nuevoRol,
  })
  return data
}

export async function desactivarUsuario(id) {
  const { data } = await api.patch(`/usuarios/usuarios/${id}/desactivar/`)
  return data
}

export async function buscarClientes(q = "") {
  const { data } = await api.get("/usuarios/clientes/", {
    params: q.trim() ? { q: q.trim() } : undefined,
  })
  return data
}
