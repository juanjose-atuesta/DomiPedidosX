import { Navigate, useLocation, useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { moneda } from "../../utils/formato"
import { ETIQUETA_ESTADO, textoTipoPedido } from "../../utils/pedidos"

export default function PedidoRecibido() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const pedido = state?.pedido

  if (!pedido) return <Navigate to="/cliente/pedidos" replace />

  return (
    <ClienteLayout titulo="Pedido recibido" volverA="/cliente/pedidos" barra>
      <MensajeAlerta tipo="exito">¡Recibimos tu pedido! La sede ya puede empezar a prepararlo.</MensajeAlerta>

      <section className="flex flex-col gap-3 rounded-xl border border-borde bg-white p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-titulo text-2xl font-semibold text-texto">Pedido #{pedido.id}</h2>
          <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
        </div>
        <p className="text-sm text-texto-sec">
          {pedido.sede_nombre} · {textoTipoPedido(pedido.tipo)}
        </p>
        {pedido.direccion_entrega && (
          <p className="text-sm text-texto-sec">Entrega en: {pedido.direccion_entrega}</p>
        )}

        <ul className="flex flex-col gap-2 border-t border-borde pt-3">
          {pedido.detalles.map((detalle) => (
            <li key={detalle.id} className="flex justify-between gap-3 text-sm text-texto">
              <div>
                <p>
                  {detalle.cantidad} × {detalle.nombre_producto}
                </p>
                {detalle.opciones.length > 0 && (
                  <p className="text-xs text-texto-sec">
                    {detalle.opciones.map((o) => o.nombre_opcion).join(", ")}
                  </p>
                )}
              </div>
              <span>{moneda(detalle.subtotal)}</span>
            </li>
          ))}
        </ul>

        <div className="flex items-center justify-between border-t border-borde pt-3">
          <span className="font-semibold text-texto">Total</span>
          <span className="font-titulo text-2xl font-semibold text-acento">{moneda(pedido.total)}</span>
        </div>
      </section>

      <Boton anchoCompleto onClick={() => navigate("/cliente/pedidos")}>
        Ver mis pedidos
      </Boton>
      <Boton tipo="secundario" anchoCompleto onClick={() => navigate("/cliente")}>
        Volver al menú
      </Boton>
    </ClienteLayout>
  )
}
