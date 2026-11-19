import { useEffect, useState } from "react"
import Interruptor from "./Interruptor"
import MensajeAlerta from "./MensajeAlerta"
import { configurarAsignacionAutomatica, listarRepartidores } from "../api/repartos"
import { mensajeDeError } from "../utils/errores"

const INTERVALO_MS = 30000

// Repartidores de una sede con su estado y el interruptor de asignación
// automática. `version` cambia cuando algo de afuera (una asignación) obliga a recargar.
export default function PanelRepartidores({ sedeId, version, onCambioAutomatica }) {
  const [datos, setDatos] = useState({ sedeId: null, info: null })
  const [error, setError] = useState("")
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true
    const cargar = () =>
      listarRepartidores(sedeId)
        .then((info) => {
          if (!vigente) return
          setDatos({ sedeId, info })
          setError("")
        })
        .catch((err) => {
          if (vigente) setError(mensajeDeError(err, "No se pudieron cargar los repartidores."))
        })
    cargar()
    const temporizador = setInterval(cargar, INTERVALO_MS)
    return () => {
      vigente = false
      clearInterval(temporizador)
    }
  }, [sedeId, version])

  const info = datos.sedeId === sedeId ? datos.info : null

  const alternar = async (activa) => {
    if (guardando) return
    setGuardando(true)
    setError("")
    try {
      await configurarAsignacionAutomatica(sedeId, activa)
      setDatos((d) => ({ ...d, info: { ...d.info, asignacion_automatica_repartidor: activa } }))
      onCambioAutomatica?.()
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo cambiar la asignación automática."))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <section
      aria-label="Repartidores"
      className="flex flex-col gap-3 rounded-xl border border-borde bg-white p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-titulo text-xl font-semibold text-texto">Repartidores</h2>
        {info && (
          <label className="flex items-center gap-2 text-sm text-texto">
            Asignación automática
            <Interruptor
              activo={info.asignacion_automatica_repartidor}
              disabled={guardando}
              onChange={alternar}
              etiqueta="Asignación automática de repartidores"
            />
          </label>
        )}
      </div>
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {!info && !error && <p className="text-sm text-texto-sec">Cargando repartidores…</p>}
      {info?.repartidores.length === 0 && (
        <p className="text-sm text-texto-sec">Esta sede no tiene repartidores asignados.</p>
      )}
      {info && (
        <ul className="flex flex-wrap gap-2">
          {info.repartidores.map((r) => (
            <li
              key={r.id}
              className="flex items-center gap-2 rounded-full border border-borde px-3 py-1 text-sm"
            >
              <span
                aria-hidden="true"
                className={`h-2 w-2 rounded-full ${r.estado === "disponible" ? "bg-exito" : "bg-ambar"}`}
              />
              <span className="font-semibold text-texto">
                {r.nombre} {r.apellido}
              </span>
              <span className="text-texto-sec">
                {r.estado === "disponible" ? "Disponible" : "Ocupado"} · {r.pedidos_hoy} hoy
              </span>
            </li>
          ))}
        </ul>
      )}
      {info?.asignacion_automatica_repartidor && (
        <p className="text-xs text-texto-sec">
          Al quedar listo un domicilio se asigna al repartidor disponible con menos pedidos hoy.
        </p>
      )}
    </section>
  )
}
