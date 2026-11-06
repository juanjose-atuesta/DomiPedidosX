import { Navigate } from "react-router-dom"
import { useAuth } from "../context/auth-context"
import { rutaInicio } from "../utils/roles"

export default function RedirigirInicio() {
  const { usuario, cargando } = useAuth()

  if (cargando) {
    return <p className="p-8 text-texto">Cargando…</p>
  }

  return <Navigate to={usuario ? rutaInicio(usuario.rol) : "/login"} replace />
}
