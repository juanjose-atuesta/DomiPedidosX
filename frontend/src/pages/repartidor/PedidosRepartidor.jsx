import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { useAuth } from "../../context/auth-context"
import { usePedidos } from "../../hooks/usePedidos"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { formatearHora, moneda } from "../../utils/formato"
import { ETIQUETA_ESTADO, accionEstado } from "../../utils/pedidos"

const SECCIONES = [
  { estado: "en_camino", titulo: "En camino", vacio: "No llevas pedidos en camino" },
  { estado: "listo_despacho", titulo: "Listos para despacho", vacio: "No hay pedidos por despachar" },
]
const ESTADOS_REPARTO = SECCIONES.map((s) => s.estado).join(",")
const ETIQUETA_PAGO = { efectivo: "Efectivo", tarjeta: "Tarjeta", transferencia: "Transferencia" }

function textoAccion(estado) {
  return estado === "en_camino" ? "Tomar pedido y salir" : accionEstado(estado)
}

function TarjetaEntrega({ pedido, procesando, onAvanzar }) {
  return (
    <article className="flex flex-col gap-3 rounded-xl border border-borde bg-white p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-titulo text-xl font-semibold text-texto">#{pedido.id}</h3>
          <p className="text-xs text-texto-sec">
            {pedido.sede_nombre} · {formatearHora(pedido.creado_en)}
          </p>
        </div>
        <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
      </div>

      <div className="flex flex-col gap-1 text-sm text-texto">
        <p className="break-words font-semibold">{pedido.direccion_entrega}</p>
        <p>
          {pedido.cliente_nombre}
          {pedido.cliente_telefono && (
            <>
              {" · "}
              <a href={`tel:${pedido.cliente_telefono}`} className="text-primario underline">
                {pedido.cliente_telefono}
              </a>
            </>
          )}
        </p>
      </div>

      <ul className="text-sm text-texto-sec">
        {pedido.detalles.map((detalle) => (
          <li key={detalle.id}>
            {detalle.cantidad} × {detalle.nombre_producto}
          </li>
        ))}
      </ul>

      {pedido.observaciones && (
        <p className="rounded-lg bg-fondo px-3 py-2 text-xs text-texto">
          Observaciones: {pedido.observaciones}
        </p>
      )}

      <p className="text-sm font-semibold text-texto">
        Total: {moneda(Number(pedido.total))} · {ETIQUETA_PAGO[pedido.metodo_pago] ?? pedido.metodo_pago}
      </p>

      {pedido.estados_siguientes.map((estado) => (
        <Boton
          key={estado}
          anchoCompleto
          disabled={procesando}
          onClick={() => onAvanzar(pedido, estado)}
        >
          {procesando ? "Actualizando…" : textoAccion(estado)}
        </Boton>
      ))}
    </article>
  )
}

export default function PedidosRepartidor() {
  const { usuario, logout } = useAuth()
  const { sedes } = useSedesUsuario()
  const { pedidos, cargando, error, procesandoId, avanzar } = usePedidos({
    sede: "",
    estado: ESTADOS_REPARTO,
  })

  return (
    <div className="min-h-dvh bg-fondo">
      <header className="sticky top-0 z-10 flex items-center justify-between gap-3 bg-vino px-4 py-3 text-white">
        <div className="min-w-0">
          <p className="font-titulo text-xl font-semibold leading-6">DomiPedidosX</p>
          <p className="truncate text-sm text-white/80">
            {usuario?.nombre}
            {usuario?.negocio ? ` · ${usuario.negocio.nombre}` : ""}
          </p>
        </div>
        <Boton tipo="contornoClaro" pequeno className="px-4 text-sm" onClick={logout}>
          Cerrar sesión
        </Boton>
      </header>

      <main className="mx-auto flex w-full max-w-[640px] flex-col gap-6 p-4">
        <h1 className="font-titulo text-[28px] font-bold leading-9 text-texto">Mis entregas</h1>

        {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
        {sedes.length === 0 && (
          <MensajeAlerta tipo="aviso">
            No tienes sedes asignadas. Pide a un administrador que te asigne una.
          </MensajeAlerta>
        )}
        {cargando && <p className="text-sm text-texto-sec">Cargando pedidos…</p>}

        {!cargando &&
          SECCIONES.map((seccion) => {
            // El API entrega primero los recientes; se atiende primero el más antiguo.
            const delEstado = pedidos.filter((p) => p.estado === seccion.estado).reverse()
            return (
              <section key={seccion.estado} aria-label={seccion.titulo} className="flex flex-col gap-3">
                <h2 className="font-titulo text-xl font-semibold text-texto">
                  {seccion.titulo} ({delEstado.length})
                </h2>
                {delEstado.length === 0 && (
                  <p className="text-sm text-texto-sec">{seccion.vacio}</p>
                )}
                {delEstado.map((pedido) => (
                  <TarjetaEntrega
                    key={pedido.id}
                    pedido={pedido}
                    procesando={procesandoId === pedido.id}
                    onAvanzar={avanzar}
                  />
                ))}
              </section>
            )
          })}
      </main>
    </div>
  )
}
