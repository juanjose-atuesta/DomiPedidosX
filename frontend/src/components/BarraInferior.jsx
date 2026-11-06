import { NavLink } from "react-router-dom"
import { Casa, Pedidos, Carrito, Usuario } from "./Iconos"

const ITEMS = [
  { texto: "Inicio", ruta: "/cliente", Icono: Casa, end: true },
  { texto: "Pedidos", ruta: "/cliente/pedidos", Icono: Pedidos },
  { texto: "Carrito", ruta: "/cliente/carrito", Icono: Carrito },
  { texto: "Perfil", ruta: "/cliente/perfil", Icono: Usuario },
]

export default function BarraInferior() {
  return (
    <nav
      aria-label="Navegación principal"
      className="fixed bottom-[38px] left-1/2 flex h-14 w-[calc(100%-44px)] max-w-[386px] -translate-x-1/2 items-center justify-between rounded-full border border-borde bg-white px-2 shadow-sm"
    >
      {ITEMS.map(({ texto, ruta, Icono, end }) => (
        <NavLink
          key={ruta}
          to={ruta}
          end={end}
          className={({ isActive }) =>
            `flex w-14 flex-col items-center text-xs leading-4 ${
              isActive ? "text-primario" : "text-texto-sec"
            }`
          }
        >
          <Icono />
          {texto}
        </NavLink>
      ))}
    </nav>
  )
}