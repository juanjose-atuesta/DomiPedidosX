import BarraLateral from "../components/BarraLateral"
import CampanaNotificaciones from "../components/CampanaNotificaciones"
import { useAuth } from "../context/auth-context"
import { tieneRol } from "../utils/roles"

// Roles del panel que reciben alertas de sus sedes (HU-7.5).
const ROLES_CON_ALERTAS = ["operador", "cocina", "admin"]

export default function AdminLayout({ titulo, accion, onNotificacion, children }) {
  const { usuario } = useAuth()
  const conAlertas = tieneRol(usuario, ROLES_CON_ALERTAS)

  return (
    <div className="flex min-h-screen bg-fondo">
      <BarraLateral />
      <main className="flex min-w-0 flex-1 flex-col gap-6 p-8">
        <div className="flex items-start justify-between gap-4">
          <h1 className="font-titulo text-[40px] font-bold leading-[48px] text-texto">
            {titulo}
          </h1>
          <div className="flex items-center gap-3">
            {accion}
            {conAlertas && <CampanaNotificaciones onNuevas={onNotificacion} />}
          </div>
        </div>
        {children}
      </main>
    </div>
  )
}
