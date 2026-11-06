import { NavLink } from "react-router-dom"
import { useAuth } from "../context/auth-context"
import { tieneRol } from "../utils/roles"

const ENLACES = [
  { texto: "Usuarios", ruta: "/admin/usuarios", roles: ["admin"] },
  { texto: "Sedes", ruta: "/admin/sedes", roles: ["admin"] },
  { texto: "Pedidos", ruta: "/operador/pedidos", roles: ["operador", "admin"] },
  { texto: "Tablero de cocina", ruta: "/cocina", roles: ["cocina", "operador", "admin"] },
  { texto: "Categorías", ruta: "/operador/categorias", roles: ["operador", "admin"] },
  { texto: "Productos", ruta: "/operador/productos", roles: ["operador", "admin"] },
  { texto: "Promociones", ruta: "/operador/promociones", roles: ["operador", "admin"] },
  { texto: "Inventario", ruta: "/operador/inventario", roles: ["operador", "admin"] },
]

const BASE = "flex w-full items-center rounded-lg px-4 py-3 text-base font-semibold"

export default function BarraLateral() {
  const { usuario, logout } = useAuth()
  const enlaces = ENLACES.filter(({ roles }) => tieneRol(usuario, roles))

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col gap-[10px] bg-vino p-4">
      <p className="font-titulo text-[28px] font-semibold leading-9 text-white">DomiPedidosX</p>
      {usuario?.negocio && (
        <p className="truncate text-sm text-white/80">{usuario.negocio.nombre}</p>
      )}
      <nav className="flex flex-col gap-[10px]">
        {enlaces.map(({ texto, ruta }) => (
          <NavLink
            key={ruta}
            to={ruta}
            className={({ isActive }) =>
              `${BASE} ${isActive ? "bg-ambar text-texto" : "text-white hover:bg-white/10"}`
            }
          >
            {texto}
          </NavLink>
        ))}
      </nav>
      <button
        type="button"
        onClick={logout}
        className={`${BASE} mt-auto text-left text-white hover:bg-white/10`}
      >
        Cerrar sesión
      </button>
    </aside>
  )
}
