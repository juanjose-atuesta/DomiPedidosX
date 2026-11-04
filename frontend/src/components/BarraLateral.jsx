import { NavLink } from "react-router-dom"

const ENLACES = [
  { texto: "Usuarios", ruta: "/admin/usuarios" },
  { texto: "Sedes", ruta: "/admin/sedes" },
  { texto: "Categorías", ruta: "/operador/categorias" },
  { texto: "Productos", ruta: "/operador/productos" },
  { texto: "Promociones", ruta: "/operador/promociones" },
  { texto: "Inventario", ruta: "/operador/inventario" },
]

const BASE = "flex w-full items-center rounded-lg px-4 py-3 text-base font-semibold"

export default function BarraLateral() {
  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col gap-[10px] bg-vino p-4">
      <p className="font-titulo text-[28px] font-semibold leading-9 text-white">DomiPedidosX</p>
      <nav className="flex flex-col gap-[10px]">
        {ENLACES.map(({ texto, ruta }) => (
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
      <NavLink to="/login" className={`${BASE} mt-auto text-white hover:bg-white/10`}>
        Cerrar sesión
      </NavLink>
    </aside>
  )
}