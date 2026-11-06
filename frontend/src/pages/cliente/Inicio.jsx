import { useState } from "react"
import { useNavigate } from "react-router-dom"
import ChipCategoria from "../../components/ChipCategoria"
import TarjetaProducto from "../../components/TarjetaProducto"
import { Lupa, UbicacionPin } from "../../components/Iconos"
import BarraInferior from "../../components/BarraInferior"
import { iconoBolsaRoja } from "../../assets"
import { CATEGORIAS, PRODUCTOS } from "../../data/productos"

const FONDO = {
  background: "linear-gradient(to top, #fff8f1 84%, #9d0208 127.76%)",
  backgroundAttachment: "fixed",
}

const SECCIONES = [
  { titulo: "Los más vendidos", icono: "🏅", ids: [1, 2, 4, 3] },
  { titulo: "Promociones", icono: "🔥", ids: [1, 4] },
  { titulo: "Combos deli", icono: "😋", ids: [1, 2, 3] },
]

export default function Inicio() {
  const navigate = useNavigate()
  const [categoria, setCategoria] = useState("Todo")
  const [busqueda, setBusqueda] = useState("")

  const texto = busqueda.trim().toLowerCase()

  const filtrar = (ids) =>
    ids
      .map((id) => PRODUCTOS.find((p) => p.id === id))
      .filter(Boolean)
      .filter((p) => p.activo)
      .filter((p) => categoria === "Todo" || p.categoria === categoria)
      .filter((p) => p.nombre.toLowerCase().includes(texto))

  const secciones = SECCIONES.map((s) => ({ ...s, productos: filtrar(s.ids) })).filter(
    (s) => s.productos.length > 0,
  )

  return (
    <div className="flex h-dvh justify-center pb-[106px]" style={FONDO}>
      <div className="h-full w-full max-w-[430px] overflow-y-auto pb-4">
        <header className="flex items-center justify-between px-[19px] pt-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium tracking-wide text-primario">DomiPedidosX</span>
            {iconoBolsaRoja && <img src={iconoBolsaRoja} alt="" className="h-[27px] w-[27px] object-cover" />}
          </div>
          <button
            type="button"
            onClick={() => navigate("/cliente/direcciones")}
            className="flex items-center gap-2 text-sm font-medium text-primario"
          >
            <UbicacionPin className="h-5 w-5" />
            Mi dirección
          </button>
        </header>

        <label className="mx-6 mt-4 flex h-9 items-center gap-2 rounded-full bg-fondo px-4">
          <Lupa className="h-5 w-5 shrink-0 text-primario" />
          <input
            type="search"
            aria-label="Buscar productos"
            placeholder="Buscar productos"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full bg-transparent text-sm text-texto outline-none placeholder:text-texto-sec"
          />
        </label>

        <div className="mt-8 flex gap-[14px] overflow-x-auto px-4 pb-1">
          {["Todo", ...CATEGORIAS].map((c) => (
            <ChipCategoria key={c} activo={categoria === c} onClick={() => setCategoria(c)}>
              {c}
            </ChipCategoria>
          ))}
        </div>

        <main className="mt-6 flex flex-col gap-6 px-4">
          {secciones.length === 0 && (
            <p className="py-10 text-center text-sm text-texto-sec">No encontramos productos</p>
          )}

          {secciones.map((s) => (
            <section key={s.titulo} className="flex flex-col gap-2">
              <h2 className="flex items-center gap-1 text-base font-semibold text-black">
                <span aria-hidden="true">{s.icono}</span>
                {s.titulo}
              </h2>
              <div className="flex gap-[21px] overflow-x-auto pb-2">
                {s.productos.map((p) => {
                  const agotado = !p.disponible
                  return (
                    <div
                      key={p.id}
                      className={`w-[250px] shrink-0 ${agotado ? "" : "cursor-pointer"}`}
                      onClick={agotado ? undefined : () => navigate(`/cliente/producto/${p.id}`)}
                    >
                      <TarjetaProducto
                        nombre={p.nombre}
                        descripcion={p.descripcion}
                        tiempo={p.tiempo}
                        precio={p.precio}
                        agotado={agotado}
                        onAgregar={(e) => {
                          e.stopPropagation()
                          navigate(`/cliente/producto/${p.id}`)
                        }}
                      />
                    </div>
                  )
                })}
              </div>
            </section>
          ))}
        </main>
      </div>

      <BarraInferior />
    </div>
  )
}