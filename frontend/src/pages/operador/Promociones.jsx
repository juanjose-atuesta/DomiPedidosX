import { useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { PROMOCIONES, formatearFecha } from "../../data/promociones"

const COLUMNAS = "grid grid-cols-[1.4fr_0.6fr_1.2fr_0.7fr_120px_250px] items-center gap-4"
const TITULOS = ["Promoción", "Descuento", "Vigencia", "Cupo diario", "Estado", "Acciones"]
const ETIQUETA = { Activa: "entregado", Vencida: "cancelado", Inactiva: "recibido" }

export default function Promociones() {
  const navigate = useNavigate()
  const [promociones, setPromociones] = useState(PROMOCIONES)
  const [aDesactivar, setADesactivar] = useState(null)

  const desactivar = () => {
    setPromociones((ps) =>
      ps.map((p) => (p.id === aDesactivar.id ? { ...p, estado: "Inactiva" } : p)),
    )
    setADesactivar(null)
  }

  return (
    <AdminLayout
      titulo="Promociones"
      accion={<Boton onClick={() => navigate("/operador/promociones/nueva")}>Nueva promoción</Boton>}
    >
      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[960px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {promociones.map((p) => (
            <div key={p.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
              <p>{p.nombre}</p>
              <p>{p.descuento}%</p>
              <p>
                {formatearFecha(p.inicio)} – {formatearFecha(p.fin)}
              </p>
              <p>{p.cupo}</p>
              <div>
                <EtiquetaEstado estado={ETIQUETA[p.estado]}>{p.estado}</EtiquetaEstado>
              </div>
              <div className="flex items-center gap-2">
                <Boton tipo="secundario" onClick={() => navigate(`/operador/promociones/${p.id}/editar`)}>
                  Editar
                </Boton>
                <Boton
                  tipo="secundario"
                  disabled={p.estado !== "Activa"}
                  onClick={() => setADesactivar(p)}
                >
                  Desactivar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ModalConfirmacion
        abierto={Boolean(aDesactivar)}
        titulo="¿Desactivar promoción?"
        texto="Dejará de aplicarse a los pedidos nuevos. Los pedidos anteriores conservan el descuento."
        textoConfirmar="Desactivar"
        onConfirmar={desactivar}
        onCancelar={() => setADesactivar(null)}
      />
    </AdminLayout>
  )
}