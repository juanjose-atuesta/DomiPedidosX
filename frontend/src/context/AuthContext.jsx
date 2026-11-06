import { useEffect, useState } from "react"
import {
  actualizarPerfil as actualizarPerfilApi,
  iniciarSesion,
  obtenerPerfil,
} from "../api/auth"
import { guardarTokens, limpiarTokens, obtenerAccess } from "../api/cliente"
import { AuthContext } from "./auth-context"

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let activo = true

    async function restaurarSesion() {
      if (!obtenerAccess()) {
        setCargando(false)
        return
      }
      try {
        const perfil = await obtenerPerfil()
        if (activo) setUsuario(perfil)
      } catch {
        limpiarTokens()
        if (activo) setUsuario(null)
      } finally {
        if (activo) setCargando(false)
      }
    }

    restaurarSesion()
    return () => {
      activo = false
    }
  }, [])

  async function login({ email, password }) {
    const tokens = await iniciarSesion({ email, password })
    guardarTokens({ access: tokens.access, refresh: tokens.refresh })
    const perfil = await obtenerPerfil()
    setUsuario(perfil)
    return perfil
  }

  function logout() {
    limpiarTokens()
    setUsuario(null)
  }

  async function actualizarPerfil(datos) {
    const perfil = await actualizarPerfilApi(datos)
    setUsuario(perfil)
    return perfil
  }

  const valor = {
    usuario,
    cargando,
    autenticado: Boolean(usuario),
    login,
    logout,
    actualizarPerfil,
  }

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
