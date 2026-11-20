import { useEffect, useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Interruptor from "../../components/Interruptor"
import MensajeAlerta from "../../components/MensajeAlerta"
import {
  actualizarConfiguracionCorreos,
  obtenerConfiguracionCorreos,
} from "../../api/notificaciones"
import { mensajeDeError } from "../../utils/errores"

const EVENTOS = [
  { campo: "confirmacion", titulo: "Confirmación del pedido", texto: "Al registrarse un pedido nuevo." },
  { campo: "cambio_estado", titulo: "Cambio de estado", texto: "Cuando el pedido pasa a preparación, listo, en camino o entregado." },
  { campo: "cancelacion", titulo: "Cancelación", texto: "Cuando el cliente cancela o la sede rechaza el pedido (incluye el motivo)." },
  { campo: "asignacion_repartidor", titulo: "Repartidor asignado", texto: "Cuando un repartidor queda a cargo del domicilio." },
]

// Correos que el negocio envía a sus clientes, por tipo de evento (HU-8.10).
export default function Correos() {
  const [config, setConfig] = useState(null)
  const [guardando, setGuardando] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    let vigente = true
    obtenerConfiguracionCorreos()
      .then((datos) => {
        if (vigente) setConfig(datos)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar la configuración."))
      })
    return () => {
      vigente = false
    }
  }, [])

  const cambiar = async (campo, valor) => {
    if (guardando) return
    setGuardando(campo)
    setError("")
    try {
      setConfig(await actualizarConfiguracionCorreos({ [campo]: valor }))
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar el cambio."))
    } finally {
      setGuardando("")
    }
  }

  return (
    <AdminLayout titulo="Correos a clientes">
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {!config && !error && <MensajeAlerta tipo="info">Cargando…</MensajeAlerta>}
      {config && (
        <section className="flex max-w-[720px] flex-col rounded-xl border border-borde bg-white p-2">
          {EVENTOS.map(({ campo, titulo, texto }) => (
            <div
              key={campo}
              className="flex items-center justify-between gap-4 border-b border-borde px-4 py-4 last:border-0"
            >
              <div>
                <p className="font-semibold text-texto">{titulo}</p>
                <p className="text-sm text-texto-sec">{texto}</p>
              </div>
              <Interruptor
                activo={config[campo]}
                disabled={Boolean(guardando)}
                onChange={(valor) => cambiar(campo, valor)}
                etiqueta={titulo}
              />
            </div>
          ))}
        </section>
      )}
      <p className="text-sm text-texto-sec">
        Los cambios se guardan al instante y aplican a todas las sedes del negocio. Los clientes
        registrados sin correo no reciben mensajes.
      </p>
    </AdminLayout>
  )
}
