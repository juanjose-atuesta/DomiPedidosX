import api from "./cliente"

export async function registrarCliente(datos) {
  const { data } = await api.post("/usuarios/registro/", datos)
  return data
}

export async function registrarNegocio(datos) {
  const { data } = await api.post("/usuarios/registro-negocio/", datos)
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

export async function solicitarRecuperacion(email) {
  const { data } = await api.post("/usuarios/password-reset/", { email })
  return data
}

export async function confirmarRecuperacion({ uidb64, token, nuevaContrasena }) {
  const { data } = await api.post("/usuarios/password-reset/confirmar/", {
    uidb64,
    token,
    new_password: nuevaContrasena,
  })
  return data
}

export async function consultarActivacion(token) {
  const { data } = await api.get(`/usuarios/activar-cuenta/${encodeURIComponent(token)}/`)
  return data
}

export async function activarCuenta({ token, password, passwordConfirmacion }) {
  const { data } = await api.post("/usuarios/activar-cuenta/", {
    token,
    password,
    password_confirmacion: passwordConfirmacion,
  })
  return data
}

export async function desactivarMiCuenta(password) {
  const { data } = await api.patch("/usuarios/me/desactivar/", { password })
  return data
}
