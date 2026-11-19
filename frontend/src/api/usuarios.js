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

export async function reenviarActivacion(id) {
  const { data } = await api.post(`/usuarios/usuarios/${id}/reenviar-activacion/`)
  return data
}

// Alta rápida de un cliente desde el panel del operador (correo opcional).
export async function registrarClienteRapido(datos) {
  const { data } = await api.post("/usuarios/clientes/", datos)
  return data
}
