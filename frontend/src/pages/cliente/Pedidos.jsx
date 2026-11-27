import { useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { cancelarPedido } from "../../api/pedidos"
import { usePedidos } from "../../hooks/usePedidos"
import { mensajeDeError } from "../../utils/errores"
import { formatearFechaHora, moneda } from "../../utils/formato"
import { ETIQUETA_ESTADO, textoTipoPedido } from "../../utils/pedidos"

// El cliente espera ver cambiar su pedido: se consulta más seguido que en los paneles.
const INTERVALO_MS = 5000

function Fila({ etiqueta, valor }) {
  return (
    <div className="flex justify-between gap-3 text-sm text-texto-sec">
      <span>{etiqueta}</span>
      <span>{valor}</span>
    </div>
  )
}

export default function Pedidos() {
  const navigate = useNavigate()
  const { pedidos, cargando, error, reemplazar } = usePedidos({ intervalo: INTERVALO_MS })
  const [aCancelar, setACancelar] = useState(null)
  const [motivo, setMotivo] = useState("")
  const [cancelando, setCancelando] = useState(false)
  const [errorCancelar, setErrorCancelar] = useState("")
  const [mensaje, setMensaje] = useState("")

  const cerrar = () => {
    if (cancelando) return
    setACancelar(null)
    setMotivo("")
    setErrorCancelar("")
  }

  const confirmarCancelacion = async () => {
    if (!aCancelar || cancelando) return
    setCancelando(true)
    setErrorCancelar("")
    try {
      const actualizado = await cancelarPedido(aCancelar.id, motivo.trim())
      reemplazar(actualizado)
      setMensaje(`Pedido #${actualizado.id} cancelado.`)
      setACancelar(null)
      setMotivo("")
    } catch (err) {
      // Si la cocina ya lo tomó, el backend lo rechaza: se explica en el modal.
      setErrorCancelar(mensajeDeError(err, "No se pudo cancelar el pedido."))
    } finally {
      setCancelando(false)
    }
  }

  return (
    <ClienteLayout titulo="Mis pedidos" volverA="/cliente" barra>
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
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

          <div className="flex flex-col gap-1 border-t border-borde pt-3">
            <Fila etiqueta="Subtotal" valor={moneda(pedido.subtotal)} />
            {Number(pedido.descuento) > 0 && (
              <Fila
                etiqueta={`Descuento${pedido.promocion_nombre ? ` (${pedido.promocion_nombre})` : ""}`}
                valor={`−${moneda(pedido.descuento)}`}
              />
            )}
            {pedido.tipo === "domicilio" && (
              <Fila etiqueta="Domicilio" valor={moneda(pedido.costo_domicilio)} />
            )}
            <div className="flex items-center justify-between pt-1">
              <span className="font-semibold text-texto">Total</span>
              <span className="font-titulo text-xl font-semibold text-acento">
                {moneda(pedido.total)}
              </span>
            </div>
          </div>

          {pedido.estado === "cancelado" && pedido.motivo_cancelacion && (
            <p className="text-xs text-texto-sec">Motivo: {pedido.motivo_cancelacion}</p>
          )}

          {pedido.puede_cancelar && (
            <Boton tipo="secundario" anchoCompleto onClick={() => setACancelar(pedido)}>
              Cancelar pedido
            </Boton>
          )}

          {(pedido.estado === "en_camino" || pedido.estado === "en_preparacion") && (
            <Boton anchoCompleto onClick={() => navigate(`/cliente/seguimiento/${pedido.id}`)}>
              Ver seguimiento en mapa
            </Boton>
          )}
          
        </article>
      ))}

      <ModalConfirmacion
        abierto={Boolean(aCancelar)}
        titulo={`¿Cancelar el pedido #${aCancelar?.id ?? ""}?`}
        texto="Solo se puede cancelar mientras la sede no ha empezado a prepararlo."
        textoConfirmar={cancelando ? "Cancelando…" : "Sí, cancelar"}
        textoCancelar="Volver"
        onConfirmar={confirmarCancelacion}
        onCancelar={cerrar}
      >
        <CampoTexto
          etiqueta="Motivo (opcional)"
          maxLength={300}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
        />
        {errorCancelar && <MensajeAlerta tipo="error">{errorCancelar}</MensajeAlerta>}
      </ModalConfirmacion>
    </ClienteLayout>
  )
}
