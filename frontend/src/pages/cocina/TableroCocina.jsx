import { useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { usePedidos } from "../../hooks/usePedidos"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { formatearHora } from "../../utils/formato"
import { ETIQUETA_ESTADO, accionEstado, textoTipoPedido } from "../../utils/pedidos"

const COLUMNAS = [
  { estado: "recibido", titulo: "Recibidos" },
  { estado: "en_preparacion", titulo: "En preparación" },
  { estado: "listo_despacho", titulo: "Listos" },
]
const ESTADOS_TABLERO = COLUMNAS.map((c) => c.estado).join(",")
const TODAS = "todas"

function TarjetaPedido({ pedido, procesando, onAvanzar }) {
  return (
    <article className="flex flex-col gap-3 rounded-xl border border-borde bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-titulo text-xl font-semibold text-texto">#{pedido.id}</h3>
          <p className="text-xs text-texto-sec">
            {formatearHora(pedido.creado_en)} · {pedido.cliente_nombre}
          </p>
          <p className="text-xs text-texto-sec">
            {pedido.sede_nombre} · {textoTipoPedido(pedido.tipo)}
          </p>
        </div>
        <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
      </div>

      <ul className="flex flex-col gap-2">
        {pedido.detalles.map((detalle) => (
          <li key={detalle.id} className="text-sm text-texto">
            <p className="font-semibold">
              {detalle.cantidad} × {detalle.nombre_producto}
            </p>
            {detalle.opciones.length > 0 && (
              <p className="text-xs text-texto-sec">
                {detalle.opciones.map((o) => o.nombre_opcion).join(", ")}
              </p>
            )}
            {detalle.notas_producto && (
              <p className="text-xs text-acento">Nota: {detalle.notas_producto}</p>
            )}
          </li>
        ))}
      </ul>

      {pedido.observaciones && (
        <p className="rounded-lg bg-fondo px-3 py-2 text-xs text-texto">
          Observaciones: {pedido.observaciones}
        </p>
      )}

      {pedido.estados_siguientes.map((estado) => (
        <Boton
          key={estado}
          anchoCompleto
          disabled={procesando}
          onClick={() => onAvanzar(pedido, estado)}
        >
          {procesando ? "Actualizando…" : accionEstado(estado)}
        </Boton>
      ))}
    </article>
  )
}

export default function TableroCocina() {
  const { sedes, cargando: cargandoSedes, error: errorSedes, esAdmin } = useSedesUsuario()
  const [sede, setSede] = useState(TODAS)
  const { pedidos, cargando, error, procesandoId, avanzar } = usePedidos({
    sede: sede === TODAS ? "" : sede,
    estado: ESTADOS_TABLERO,
  })

  const sinSedes = !cargandoSedes && !esAdmin && sedes.length === 0

  return (
    <AdminLayout titulo="Tablero de cocina">
      {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {sinSedes && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
        </MensajeAlerta>
      )}

      {sedes.length > 1 && (
        <div className="w-full max-w-[320px]">
          <CampoSelect
            etiqueta="Sede"
            opciones={[
              { valor: TODAS, etiqueta: "Todas mis sedes" },
              ...sedes.map((s) => ({ valor: s.id, etiqueta: s.nombre })),
            ]}
            value={sede}
            onChange={(e) => setSede(e.target.value)}
          />
        </div>
      )}

      <div className="grid items-start gap-4 lg:grid-cols-3">
        {COLUMNAS.map((columna) => {
          // El API entrega primero los recientes; en cocina se atiende el más antiguo primero.
          const delEstado = pedidos.filter((p) => p.estado === columna.estado).reverse()
          return (
            <section
              key={columna.estado}
              aria-label={columna.titulo}
              className="flex flex-col gap-3 rounded-xl bg-borde/50 p-3"
            >
              <h2 className="font-titulo text-xl font-semibold text-texto">
                {columna.titulo} ({delEstado.length})
              </h2>
              {cargando && <p className="text-sm text-texto-sec">Cargando pedidos…</p>}
              {!cargando && delEstado.length === 0 && (
                <p className="text-sm text-texto-sec">Sin pedidos</p>
              )}
              {!cargando &&
                delEstado.map((pedido) => (
                  <TarjetaPedido
                    key={pedido.id}
                    pedido={pedido}
                    procesando={procesandoId === pedido.id}
                    onAvanzar={avanzar}
                  />
                ))}
            </section>
          )
        })}
      </div>
    </AdminLayout>
  )
}
