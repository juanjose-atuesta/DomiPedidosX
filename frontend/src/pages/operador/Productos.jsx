import { useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import ChipCategoria from "../../components/ChipCategoria"
import Interruptor from "../../components/Interruptor"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { CATEGORIAS, PRODUCTOS } from "../../data/productos"

const COLUMNAS = "grid grid-cols-[1.4fr_1.1fr_0.7fr_0.7fr_120px_250px] items-center gap-4"
const TITULOS = ["Producto", "Categoría", "Precio", "Tiempo", "Disponible", "Acciones"]

export default function Productos() {
  const navigate = useNavigate()
  const [productos, setProductos] = useState(PRODUCTOS)
  const [categoria, setCategoria] = useState("Todas")
  const [aDesactivar, setADesactivar] = useState(null)

  const visibles =
    categoria === "Todas" ? productos : productos.filter((p) => p.categoria === categoria)

  const cambiarDisponible = (id, valor) =>
    setProductos((ps) => ps.map((p) => (p.id === id ? { ...p, disponible: valor } : p)))

  const desactivar = () => {
    setProductos((ps) =>
      ps.map((p) => (p.id === aDesactivar.id ? { ...p, activo: false, disponible: false } : p)),
    )
    setADesactivar(null)
  }

  return (
    <AdminLayout
      titulo="Productos"
      accion={<Boton onClick={() => navigate("/operador/productos/nuevo")}>Nuevo producto</Boton>}
    >
      <div className="flex flex-wrap gap-2">
        {["Todas", ...CATEGORIAS].map((c) => (
          <ChipCategoria key={c} activo={categoria === c} onClick={() => setCategoria(c)}>
            {c}
          </ChipCategoria>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[900px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {visibles.length === 0 && (
            <p className="py-6 text-sm text-texto-sec">No hay productos en esta categoría</p>
          )}

          {visibles.map((p) => (
            <div
              key={p.id}
              className={`${COLUMNAS} py-3 text-sm leading-5 text-texto ${p.activo ? "" : "opacity-60"}`}
            >
              <p>{p.nombre}</p>
              <p>{p.categoria}</p>
              <p>${p.precio.toLocaleString("es-CO")}</p>
              <p>{p.tiempo} min</p>
              <div>
                <Interruptor
                  activo={p.disponible}
                  disabled={!p.activo}
                  etiqueta={`Disponible: ${p.nombre}`}
                  onChange={(valor) => cambiarDisponible(p.id, valor)}
                />
              </div>
              <div className="flex items-center gap-2">
                <Boton tipo="secundario" onClick={() => navigate(`/operador/productos/${p.id}/editar`)}>
                  Editar
                </Boton>
                <Boton tipo="secundario" disabled={!p.activo} onClick={() => setADesactivar(p)}>
                  Desactivar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ModalConfirmacion
        abierto={Boolean(aDesactivar)}
        titulo="¿Desactivar producto?"
        texto="Dejará de aparecer en el menú del cliente. Los pedidos anteriores conservan el producto."
        textoConfirmar="Desactivar"
        onConfirmar={desactivar}
        onCancelar={() => setADesactivar(null)}
      />
    </AdminLayout>
  )
}