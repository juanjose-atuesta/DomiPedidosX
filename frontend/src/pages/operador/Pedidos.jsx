import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { usePedidos } from "../../hooks/usePedidos"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { fechaDeHoy, formatearHora, moneda } from "../../utils/formato"
import {
  ESTADOS_PEDIDO,
  ETIQUETA_ESTADO,
  accionEstado,
  textoTipoPedido,
} from "../../utils/pedidos"

const COLUMNAS =
  "grid grid-cols-[50px_80px_0.9fr_1.1fr_0.9fr_130px_80px_235px] items-center gap-4"
const TITULOS = ["Pedido", "Hora", "Cliente", "Productos", "Sede y tipo", "Estado", "Total", "Acción"]
const TODOS = "todos"

export default function Pedidos() {
  const navigate = useNavigate()
  const location = useLocation()
  const { sedes, cargando: cargandoSedes, error: errorSedes, esAdmin } = useSedesUsuario()
  const [sede, setSede] = useState(TODOS)
  const [estado, setEstado] = useState(TODOS)
  const [fecha, setFecha] = useState(fechaDeHoy)
  const { pedidos, cargando, error, procesandoId, avanzar } = usePedidos({
    sede: sede === TODOS ? "" : sede,
    estado: estado === TODOS ? "" : estado,
    fecha,
  })

  const sinSedes = !cargandoSedes && !esAdmin && sedes.length === 0

  // Tras avanzar un pedido puede dejar de cumplir el filtro de estado.
  const visibles = estado === TODOS ? pedidos : pedidos.filter((p) => p.estado === estado)

  return (
    <AdminLayout
      titulo="Pedidos"
      accion={<Boton onClick={() => navigate("/operador/pedidos/nuevo")}>Nuevo pedido</Boton>}
    >
      {location.state?.mensaje && (
        <MensajeAlerta tipo="exito">{location.state.mensaje}</MensajeAlerta>
      )}
      {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {sinSedes && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
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

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[1100px]">
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
                </div>
                <p>{moneda(pedido.total)}</p>
                <div>
                  {pedido.estados_siguientes.map((siguiente) => (
                    <Boton
                      key={siguiente}
                      tipo="secundario"
                      disabled={procesandoId === pedido.id}
                      onClick={() => avanzar(pedido, siguiente)}
                    >
                      {accionEstado(siguiente)}
                    </Boton>
                  ))}
                </div>
              </div>
            ))}
        </div>
      </div>
    </AdminLayout>
  )
}
