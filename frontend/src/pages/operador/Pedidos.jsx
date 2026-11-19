import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import PanelRepartidores from "../../components/PanelRepartidores"
import { rechazarPedido } from "../../api/pedidos"
import { asignarRepartidor, listarRepartidores } from "../../api/repartos"
import { usePedidos } from "../../hooks/usePedidos"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { mensajeDeError } from "../../utils/errores"
import { fechaDeHoy, formatearHora, moneda } from "../../utils/formato"
import {
  ESTADOS_PEDIDO,
  ETIQUETA_ESTADO,
  accionEstado,
  textoTipoPedido,
} from "../../utils/pedidos"

const COLUMNAS =
  "grid grid-cols-[50px_70px_0.9fr_1.1fr_0.9fr_130px_80px_140px_220px] items-center gap-4"
const TITULOS = ["Pedido", "Hora", "Cliente", "Productos", "Sede y tipo", "Estado", "Total", "Repartidor", "Acción"]
const TODOS = "todos"
const MOTIVO_MINIMO = 10

// Elige entre los repartidores disponibles de la sede del pedido.
function ModalAsignar({ pedido, onAsignado, onCerrar }) {
  const [repartidores, setRepartidores] = useState(null)
  const [elegido, setElegido] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let vigente = true
    listarRepartidores(pedido.sede_id)
      .then((info) => {
        if (vigente) setRepartidores(info.repartidores)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar los repartidores."))
      })
    return () => {
      vigente = false
    }
  }, [pedido.sede_id])

  const disponibles = (repartidores ?? []).filter((r) => r.estado === "disponible")
  const valor = elegido || disponibles[0]?.id || ""

  const asignar = async () => {
    if (!valor || enviando) return
    setEnviando(true)
    setError("")
    try {
      onAsignado(await asignarRepartidor(pedido.id, valor))
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo asignar el repartidor."))
      setEnviando(false)
    }
  }

  return (
    <ModalConfirmacion
      abierto
      titulo={`Asignar repartidor al pedido #${pedido.id}`}
      textoConfirmar={enviando ? "Asignando…" : "Asignar"}
      onConfirmar={asignar}
      onCancelar={onCerrar}
    >
      {repartidores === null && !error && <p className="text-sm text-texto-sec">Cargando…</p>}
      {repartidores && disponibles.length === 0 && (
        <MensajeAlerta tipo="aviso">No hay repartidores disponibles en {pedido.sede_nombre}.</MensajeAlerta>
      )}
      {disponibles.length > 0 && (
        <CampoSelect
          etiqueta="Repartidor disponible"
          opciones={disponibles.map((r) => ({
            valor: r.id,
            etiqueta: `${r.nombre} ${r.apellido} · ${r.pedidos_hoy} pedidos hoy`,
          }))}
          value={valor}
          onChange={(e) => setElegido(e.target.value)}
        />
      )}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
    </ModalConfirmacion>
  )
}

function ModalRechazar({ pedido, onRechazado, onCerrar }) {
  const [motivo, setMotivo] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)
  const corto = motivo.trim().length < MOTIVO_MINIMO

  const rechazar = async () => {
    if (enviando) return
    if (corto) {
      setError(`Escribe un motivo de al menos ${MOTIVO_MINIMO} caracteres: el cliente lo verá.`)
      return
    }
    setEnviando(true)
    setError("")
    try {
      onRechazado(await rechazarPedido(pedido.id, motivo.trim()))
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo rechazar el pedido."))
      setEnviando(false)
    }
  }

  return (
    <ModalConfirmacion
      abierto
      titulo={`¿Rechazar el pedido #${pedido.id}?`}
      texto="El pedido se cancela, las existencias vuelven al inventario y el cliente ve el motivo."
      textoConfirmar={enviando ? "Rechazando…" : "Rechazar pedido"}
      textoCancelar="Volver"
      onConfirmar={rechazar}
      onCancelar={onCerrar}
    >
      <CampoTexto
        etiqueta={`Motivo (mínimo ${MOTIVO_MINIMO} caracteres)`}
        maxLength={300}
        value={motivo}
        error={error}
        onChange={(e) => setMotivo(e.target.value)}
      />
      <p className="text-xs text-texto-sec">{motivo.trim().length} caracteres</p>
    </ModalConfirmacion>
  )
}

function Acciones({ pedido, procesando, onAvanzar, onRechazar, onAsignar }) {
  if (pedido.estado === "recibido") {
    return (
      <div className="flex gap-2">
        <Boton tipo="secundario" pequeno disabled={procesando} onClick={() => onAvanzar(pedido, "en_preparacion")}>
          Aceptar
        </Boton>
        <Boton tipo="texto" pequeno disabled={procesando} onClick={() => onRechazar(pedido)}>
          Rechazar
        </Boton>
      </div>
    )
  }
  return (
    <div className="flex flex-wrap gap-2">
      {pedido.esperando_repartidor && (
        <Boton tipo="secundario" pequeno disabled={procesando} onClick={() => onAsignar(pedido)}>
          Asignar repartidor
        </Boton>
      )}
      {pedido.estados_siguientes.map((siguiente) => (
        <Boton
          key={siguiente}
          tipo="secundario"
          pequeno
          disabled={procesando}
          onClick={() => onAvanzar(pedido, siguiente)}
        >
          {accionEstado(siguiente)}
        </Boton>
      ))}
    </div>
  )
}

export default function Pedidos() {
  const navigate = useNavigate()
  const location = useLocation()
  const { sedes, cargando: cargandoSedes, error: errorSedes, esAdmin } = useSedesUsuario()
  const [sede, setSede] = useState(TODOS)
  const [estado, setEstado] = useState(TODOS)
  const [fecha, setFecha] = useState(fechaDeHoy)
  const [aRechazar, setARechazar] = useState(null)
  const [aAsignar, setAAsignar] = useState(null)
  const [mensaje, setMensaje] = useState(location.state?.mensaje ?? "")
  const [version, setVersion] = useState(0)
  const { pedidos, cargando, error, procesandoId, avanzar, reemplazar } = usePedidos({
    sede: sede === TODOS ? "" : sede,
    estado: estado === TODOS ? "" : estado,
    fecha,
  })

  const sinSedes = !cargandoSedes && !esAdmin && sedes.length === 0
  const sedePanel = sede !== TODOS ? sede : sedes.length === 1 ? sedes[0].id : ""

  // Tras avanzar un pedido puede dejar de cumplir el filtro de estado.
  const visibles = estado === TODOS ? pedidos : pedidos.filter((p) => p.estado === estado)
  const sinRepartidor = pedidos.filter((p) => p.esperando_repartidor && p.asignacion_automatica)

  const actualizar = (pedido, texto) => {
    reemplazar(pedido)
    setMensaje(texto)
    setVersion((v) => v + 1)
  }

  return (
    <AdminLayout
      titulo="Pedidos"
      accion={<Boton onClick={() => navigate("/operador/pedidos/nuevo")}>Nuevo pedido</Boton>}
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {sinSedes && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
        </MensajeAlerta>
      )}
      {sinRepartidor.length > 0 && (
        <MensajeAlerta tipo="aviso">
          {sinRepartidor.length === 1
            ? `El pedido #${sinRepartidor[0].id} está listo pero no hay repartidores disponibles.`
            : `${sinRepartidor.length} pedidos están listos pero no hay repartidores disponibles.`}{" "}
          Se asignarán cuando uno se libere, o puedes asignarlos manualmente.
        </MensajeAlerta>
      )}

      <div className="flex flex-wrap items-end gap-4">
        <CampoSelect
          className="w-[240px]"
          etiqueta="Sede"
          opciones={[
            { valor: TODOS, etiqueta: esAdmin ? "Todas las sedes" : "Todas mis sedes" },
            ...sedes.map((s) => ({ valor: s.id, etiqueta: s.nombre })),
          ]}
          value={sede}
          onChange={(e) => setSede(e.target.value)}
        />
        <CampoSelect
          className="w-[220px]"
          etiqueta="Estado"
          opciones={[{ valor: TODOS, etiqueta: "Todos los estados" }, ...ESTADOS_PEDIDO]}
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
        />
        <CampoTexto
          className="w-[180px]"
          etiqueta="Fecha"
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
        />
      </div>

      {sedePanel ? (
        <PanelRepartidores
          sedeId={sedePanel}
          version={version}
          onCambioAutomatica={() => setVersion((v) => v + 1)}
        />
      ) : (
        sedes.length > 1 && (
          <p className="text-sm text-texto-sec">
            Elige una sede para ver sus repartidores y la asignación automática.
          </p>
        )
      )}

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[1250px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((titulo) => (
              <p key={titulo}>{titulo}</p>
            ))}
          </div>

          {cargando && <p className="py-6 text-sm text-texto-sec">Cargando pedidos…</p>}
          {!cargando && visibles.length === 0 && (
            <p className="py-6 text-sm text-texto-sec">No hay pedidos con estos filtros.</p>
          )}

          {!cargando &&
            visibles.map((pedido) => (
              <div key={pedido.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
                <p className="font-semibold">#{pedido.id}</p>
                <p>{formatearHora(pedido.creado_en)}</p>
                <div>
                  <p>{pedido.cliente_nombre}</p>
                  <p className="text-xs text-texto-sec">{pedido.cliente_telefono}</p>
                </div>
                <p>
                  {pedido.detalles
                    .map((d) => `${d.cantidad} × ${d.nombre_producto}`)
                    .join(", ")}
                </p>
                <div>
                  <p>{pedido.sede_nombre}</p>
                  <p className="text-xs text-texto-sec">{textoTipoPedido(pedido.tipo)}</p>
                </div>
                <div>
                  <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
                  {pedido.estado === "cancelado" && pedido.motivo_cancelacion && (
                    <p className="mt-1 text-xs text-texto-sec">{pedido.motivo_cancelacion}</p>
                  )}
                </div>
                <p>{moneda(pedido.total)}</p>
                <p className={pedido.esperando_repartidor ? "text-ambar" : ""}>
                  {pedido.repartidor_nombre ??
                    (pedido.esperando_repartidor ? "Sin asignar" : "—")}
                </p>
                <Acciones
                  pedido={pedido}
                  procesando={procesandoId === pedido.id}
                  onAvanzar={async (p, siguiente) => {
                    await avanzar(p, siguiente)
                    // Quedar listo puede asignar (u ocupar) un repartidor.
                    setVersion((v) => v + 1)
                  }}
                  onRechazar={setARechazar}
                  onAsignar={setAAsignar}
                />
              </div>
            ))}
        </div>
      </div>

      {aRechazar && (
        <ModalRechazar
          key={aRechazar.id}
          pedido={aRechazar}
          onCerrar={() => setARechazar(null)}
          onRechazado={(pedido) => {
            setARechazar(null)
            actualizar(pedido, `Pedido #${pedido.id} rechazado. El cliente verá el motivo.`)
          }}
        />
      )}
      {aAsignar && (
        <ModalAsignar
          key={aAsignar.id}
          pedido={aAsignar}
          onCerrar={() => setAAsignar(null)}
          onAsignado={(pedido) => {
            setAAsignar(null)
            actualizar(pedido, `Pedido #${pedido.id} asignado a ${pedido.repartidor_nombre}.`)
          }}
        />
      )}
    </AdminLayout>
  )
}
