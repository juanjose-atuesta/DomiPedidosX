import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { usePedidos } from "../../hooks/usePedidos"
import { formatearFechaHora, moneda } from "../../utils/formato"
import { ETIQUETA_ESTADO, textoTipoPedido } from "../../utils/pedidos"

// El cliente espera ver cambiar su pedido: se consulta más seguido que en los paneles.
const INTERVALO_MS = 10000

export default function Pedidos() {
  const navigate = useNavigate()
  const { pedidos, cargando, error } = usePedidos({ intervalo: INTERVALO_MS })

  return (
    <ClienteLayout titulo="Mis pedidos" volverA="/cliente" barra>
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {cargando && <p className="py-10 text-center text-sm text-texto-sec">Cargando pedidos…</p>}

      {!cargando && !error && pedidos.length === 0 && (
        <>
          <p className="text-center text-sm text-texto-sec">Aún no tienes pedidos</p>
          <Boton anchoCompleto onClick={() => navigate("/cliente")}>
            Ver menú
          </Boton>
        </>
      )}

      {pedidos.map((pedido) => (
        <article
          key={pedido.id}
          className="flex flex-col gap-3 rounded-xl border border-borde bg-white p-4"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h2 className="font-titulo text-xl font-semibold text-texto">Pedido #{pedido.id}</h2>
              <p className="break-words text-sm text-texto">
                {pedido.negocio_nombre} · {pedido.sede_nombre}
              </p>
              <p className="text-xs text-texto-sec">
                {formatearFechaHora(pedido.creado_en)} · {textoTipoPedido(pedido.tipo)}
              </p>
            </div>
            <div className="shrink-0">
              <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
            </div>
          </div>

          <ul className="flex flex-col gap-1 border-t border-borde pt-3 text-sm text-texto">
            {pedido.detalles.map((detalle) => (
              <li key={detalle.id} className="flex justify-between gap-3">
                <span className="min-w-0 break-words">
                  {detalle.cantidad} × {detalle.nombre_producto}
                </span>
                <span className="shrink-0">{moneda(detalle.subtotal)}</span>
              </li>
            ))}
          </ul>

          <div className="flex items-center justify-between border-t border-borde pt-3">
            <span className="font-semibold text-texto">Total</span>
            <span className="font-titulo text-xl font-semibold text-acento">
              {moneda(pedido.total)}
            </span>
          </div>
        </article>
      ))}
    </ClienteLayout>
  )
}
