import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/auth-context"
import { tieneRol } from "../utils/roles"

export default function RutaProtegida({ roles, children }) {
  const { usuario, cargando } = useAuth()
  const location = useLocation()

  if (cargando) {
    return <p className="p-8 text-texto">Cargando…</p>
  }

  if (!usuario) {
    return <Navigate to="/iniciar-sesion" state={{ desde: location }} replace />
  }

  if (!tieneRol(usuario, roles)) {
    return <Navigate to="/acceso-denegado" replace />
  }

  return children
}
