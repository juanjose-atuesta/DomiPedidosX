import { useEffect, useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import {
  actualizarConfiguracionCapacidad,
  obtenerConfiguracionCapacidad,
} from "../../api/negocios"
import { mensajeDeError } from "../../utils/errores"

function validarPorcentaje(texto) {
  if (!/^\d+$/.test(texto.trim())) return "Escribe un número entero."
  const valor = Number(texto)
  if (valor < 1 || valor > 100) return "El porcentaje debe estar entre 1 y 100."
  return ""
}

// Porcentaje de ocupación a partir del cual se alerta a las sedes (HU-9.3).
export default function Capacidad() {
  const [config, setConfig] = useState(null)
  const [valor, setValor] = useState("")
  const [errorCampo, setErrorCampo] = useState("")
  const [error, setError] = useState("")
  const [exito, setExito] = useState("")
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true
    obtenerConfiguracionCapacidad()
      .then((datos) => {
        if (!vigente) return
        setConfig(datos)
        setValor(String(datos.porcentaje_alerta_capacidad))
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar la configuración."))
      })
    return () => {
      vigente = false
    }
  }, [])

  const guardar = async (evento) => {
    evento.preventDefault()
    if (guardando) return
    const problema = validarPorcentaje(valor)
    setErrorCampo(problema)
    setExito("")
    if (problema) return
    setGuardando(true)
    setError("")
    try {
      const datos = await actualizarConfiguracionCapacidad({
        porcentaje_alerta_capacidad: Number(valor),
      })
      setConfig(datos)
      setValor(String(datos.porcentaje_alerta_capacidad))
      setExito(
        `Guardado. Las ${datos.sedes_afectadas} sedes del negocio alertarán al llegar al ${datos.porcentaje_alerta_capacidad}% de su capacidad.`,
      )
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar el porcentaje."))
    } finally {
      setGuardando(false)
    }
  }

  const sinCambios = config && Number(valor) === config.porcentaje_alerta_capacidad

  return (
    <AdminLayout titulo="Capacidad">
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {exito && <MensajeAlerta tipo="exito">{exito}</MensajeAlerta>}
      {!config && !error && <MensajeAlerta tipo="info">Cargando…</MensajeAlerta>}
      {config && (
        <form
          onSubmit={guardar}
          className="flex max-w-[720px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <div>
            <p className="font-semibold text-texto">Porcentaje de alerta de capacidad</p>
            <p className="text-sm text-texto-sec">
              Cuando los pedidos en curso de una sede lleguen a este porcentaje de su tope, se
              avisa al personal para que se prepare. Aplica a todas las sedes del negocio desde
              que lo guardas.
            </p>
          </div>
          <div className="flex flex-wrap items-end gap-4">
            <CampoTexto
              className="w-[180px]"
              etiqueta="Porcentaje (1 a 100)"
              type="number"
              inputMode="numeric"
              min={1}
              max={100}
              step={1}
              value={valor}
              error={errorCampo}
              onChange={(e) => {
                setValor(e.target.value)
                setErrorCampo("")
                setExito("")
              }}
            />
            <Boton type="submit" disabled={guardando || sinCambios}>
              {guardando ? "Guardando…" : "Guardar"}
            </Boton>
          </div>
        </form>
      )}
    </AdminLayout>
  )
}
