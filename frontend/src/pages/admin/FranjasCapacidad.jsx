import { useCallback, useEffect, useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { useAuth } from "../../context/auth-context"
import {
  actualizarFranja,
  crearFranja,
  eliminarFranja,
  listarFranjas,
} from "../../api/cobertura"
import { mensajeDeError } from "../../utils/errores"

const DIAS = {
  1: "Lunes",
  2: "Martes",
  3: "Miércoles",
  4: "Jueves",
  5: "Viernes",
  6: "Sábado",
  7: "Domingo",
}

// Las franjas son de 1 hora: solo se puede elegir una hora en punto.
const HORAS = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}:00`)

const CAMPOS_DEL_FORMULARIO = ["dia_semana", "hora_inicio", "max_pedidos_simultaneos"]

// El backend manda "12:00:00"; se muestra "12:00".
const hhmm = (hora) => String(hora).slice(0, 5)
const horaFin = (inicio) => `${String((Number(inicio.slice(0, 2)) + 1) % 24).padStart(2, "0")}:00`

// HU-9.4: la franja de hoy está cerca del límite según su porcentaje de alerta.
const cercaDelLimite = (franja) =>
  typeof franja.pedidos_actuales === "number" &&
  (franja.pedidos_actuales / franja.max_pedidos_simultaneos) * 100 >=
    (franja.umbral_alerta_pct ?? 80)

function textoDe(valor) {
  return Array.isArray(valor) ? valor.join(" ") : String(valor)
}

// Separa los errores del backend: los de un campo van junto al campo; el resto, arriba.
function erroresDeApi(err) {
  const datos = err.response?.data
  const campos = {}
  const generales = []
  if (datos && typeof datos === "object" && !Array.isArray(datos)) {
    for (const [clave, valor] of Object.entries(datos)) {
      if (CAMPOS_DEL_FORMULARIO.includes(clave)) campos[clave] = textoDe(valor)
      else generales.push(textoDe(valor))
    }
  }
  if (!Object.keys(campos).length && !generales.length) {
    generales.push(mensajeDeError(err, "No se pudo guardar la franja."))
  }
  return { campos, general: generales.join(" ") }
}

export default function FranjasCapacidad() {
  const { id } = useParams() // el admin entra desde una sede; el operador usa la suya
  const navigate = useNavigate()
  const { usuario } = useAuth()
  const sedesPropias = usuario?.sedes ?? []
  const [sedeElegida, setSedeElegida] = useState("")
  const sedeId = id ?? (sedeElegida || sedesPropias[0]?.id)

  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState("")
  const [exito, setExito] = useState("")
  const [formulario, setFormulario] = useState(null) // { id, dia, hora, tope }
  const [errores, setErrores] = useState({ campos: {}, general: "" })
  const [guardando, setGuardando] = useState(false)

  const cargar = useCallback(async () => {
    if (!sedeId) return
    setCargando(true)
    try {
      setDatos(await listarFranjas(sedeId))
      setError("")
    } catch (err) {
      setError(mensajeDeError(err, "No se pudieron cargar las franjas."))
    } finally {
      setCargando(false)
    }
  }, [sedeId])

  useEffect(() => {
    setFormulario(null)
    setExito("")
    cargar()
  }, [cargar])

  const topeGeneral = datos?.tope_general ?? null

  const porDia = useMemo(() => {
    const grupos = {}
    for (const franja of datos?.franjas ?? []) {
      ;(grupos[franja.dia_semana] ??= []).push(franja)
    }
    return Object.entries(grupos).sort(([a], [b]) => Number(a) - Number(b))
  }, [datos])

  const abrirNueva = () => {
    setExito("")
    setErrores({ campos: {}, general: "" })
    setFormulario({ id: null, dia: 1, hora: "12:00", tope: "" })
  }

  const abrirEditar = (franja) => {
    setExito("")
    setErrores({ campos: {}, general: "" })
    setFormulario({
      id: franja.id,
      dia: franja.dia_semana,
      hora: hhmm(franja.hora_inicio),
      tope: String(franja.max_pedidos_simultaneos),
    })
  }

  const cambiar = (campo, valor) => {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
    setErrores({ campos: {}, general: "" })
  }

  const guardar = async (evento) => {
    evento.preventDefault()
    if (guardando) return
    const texto = String(formulario.tope).trim()
    let problema = ""
    if (!/^\d+$/.test(texto) || Number(texto) < 1) {
      problema = "Escribe un número entero mayor o igual a 1."
    } else if (topeGeneral != null && Number(texto) > topeGeneral) {
      problema = `No puede superar el tope general de la sede (${topeGeneral}).`
    }
    if (problema) {
      setErrores({ campos: { max_pedidos_simultaneos: problema }, general: "" })
      return
    }

    const carga = {
      dia_semana: Number(formulario.dia),
      hora_inicio: formulario.hora,
      max_pedidos_simultaneos: Number(texto),
    }
    setGuardando(true)
    try {
      if (formulario.id) await actualizarFranja(formulario.id, carga)
      else await crearFranja(sedeId, carga)
      setExito(formulario.id ? "Franja actualizada." : "Franja creada.")
      setFormulario(null)
      cargar()
    } catch (err) {
      setErrores(erroresDeApi(err))
    } finally {
      setGuardando(false)
    }
  }

  const eliminar = async (franja) => {
    const nombre = `${DIAS[franja.dia_semana]} ${hhmm(franja.hora_inicio)}`
    if (!window.confirm(`¿Eliminar la franja del ${nombre}?`)) return
    setExito("")
    try {
      await eliminarFranja(franja.id)
      setExito("Franja eliminada.")
      cargar()
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo eliminar la franja."))
    }
  }

  return (
    <AdminLayout
      titulo="Franjas de capacidad"
      accion={
        <div className="flex gap-2">
          {id && (
            <Boton tipo="secundario" onClick={() => navigate("/admin/sedes")}>
              Volver a Sedes
            </Boton>
          )}
          <Boton
            onClick={abrirNueva}
            disabled={!datos || topeGeneral == null || Boolean(formulario)}
          >
            Agregar franja
          </Boton>
        </div>
      }
    >
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {exito && <MensajeAlerta tipo="exito">{exito}</MensajeAlerta>}
      {!sedeId && (
        <MensajeAlerta tipo="info">No tienes una sede asignada.</MensajeAlerta>
      )}

      {!id && sedesPropias.length > 1 && (
        <label className="mb-4 flex max-w-[320px] flex-col text-sm">
          Sede
          <select
            value={sedeId ?? ""}
            onChange={(e) => setSedeElegida(e.target.value)}
            className="mt-1 rounded border border-borde p-2"
          >
            {sedesPropias.map((sede) => (
              <option key={sede.id} value={sede.id}>
                {sede.nombre}
              </option>
            ))}
          </select>
        </label>
      )}

      {datos && topeGeneral == null && (
        <MensajeAlerta tipo="info">
          El administrador debe definir primero el tope general de la sede.
        </MensajeAlerta>
      )}

      {formulario && (
        <form
          onSubmit={guardar}
          className="mb-6 flex max-w-[720px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <h2 className="font-titulo text-lg font-semibold text-texto">
            {formulario.id ? "Editar franja" : "Nueva franja"}
          </h2>
          {errores.general && <MensajeAlerta tipo="error">{errores.general}</MensajeAlerta>}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <label className="flex flex-col text-sm">
              Día
              <select
                value={formulario.dia}
                onChange={(e) => cambiar("dia", e.target.value)}
                className="mt-1 rounded border border-borde p-2"
              >
                {Object.entries(DIAS).map(([numero, nombre]) => (
                  <option key={numero} value={numero}>
                    {nombre}
                  </option>
                ))}
              </select>
              {errores.campos.dia_semana && (
                <span className="mt-1 text-xs text-red-700">{errores.campos.dia_semana}</span>
              )}
            </label>
            <label className="flex flex-col text-sm">
              Franja (1 hora)
              <select
                value={formulario.hora}
                onChange={(e) => cambiar("hora", e.target.value)}
                className="mt-1 rounded border border-borde p-2"
              >
                {HORAS.map((hora) => (
                  <option key={hora} value={hora}>
                    {hora} a {horaFin(hora)}
                  </option>
                ))}
              </select>
              {errores.campos.hora_inicio && (
                <span className="mt-1 text-xs text-red-700">{errores.campos.hora_inicio}</span>
              )}
            </label>
            <CampoTexto
              etiqueta={`Tope de pedidos (1 a ${topeGeneral ?? "?"})`}
              type="number"
              inputMode="numeric"
              min={1}
              max={topeGeneral ?? undefined}
              step={1}
              value={formulario.tope}
              error={errores.campos.max_pedidos_simultaneos}
              onChange={(e) => cambiar("tope", e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Boton type="submit" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar"}
            </Boton>
            <Boton tipo="secundario" type="button" onClick={() => setFormulario(null)}>
              Cancelar
            </Boton>
          </div>
        </form>
      )}

      <div className="max-w-[720px] rounded-xl border border-borde bg-white p-6">
        <h2 className="mb-1 font-titulo text-xl font-semibold text-texto">
          Topes de pedidos simultáneos
        </h2>
        <p className="mb-6 text-sm text-texto-sec">
          Cuántos pedidos en estado recibido o en preparación admite la cocina a la vez en cada
          franja de 1 hora.
          {topeGeneral != null && ` Tope general de la sede: ${topeGeneral}.`}
        </p>

        {cargando && !datos ? (
          <p className="text-sm text-texto-sec">Cargando franjas…</p>
        ) : porDia.length === 0 ? (
          <p className="text-sm text-texto-sec">Esta sede aún no tiene franjas configuradas.</p>
        ) : (
          <div className="flex flex-col gap-5">
            {porDia.map(([dia, franjas]) => (
              <section key={dia}>
                <h3 className="mb-2 font-semibold text-texto">{DIAS[dia]}</h3>
                <div className="flex flex-col gap-2">
                  {franjas.map((franja) => (
                    <div
                      key={franja.id}
                      className="flex flex-col justify-between gap-3 rounded-lg border border-borde p-3 md:flex-row md:items-center"
                    >
                      <div>
                        <p className="font-semibold text-texto">
                          {hhmm(franja.hora_inicio)} - {horaFin(hhmm(franja.hora_inicio))}
                        </p>
                        <p className="text-sm text-texto-sec">
                          Tope: <strong>{franja.max_pedidos_simultaneos} pedidos</strong>
                        </p>
                      </div>
                      {typeof franja.pedidos_actuales === "number" && (
                        <div
                          className={`rounded-lg px-3 py-1 text-sm font-semibold ${
                            cercaDelLimite(franja)
                              ? "bg-red-100 text-red-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {cercaDelLimite(franja) ? "⚠️ Cerca del límite · " : ""}
                          Ocupación: {franja.pedidos_actuales} / {franja.max_pedidos_simultaneos}
                        </div>
                      )}
                      <div className="flex gap-2">
                        <Boton tipo="secundario" onClick={() => abrirEditar(franja)}>
                          Editar
                        </Boton>
                        <Boton tipo="secundario" onClick={() => eliminar(franja)}>
                          Eliminar
                        </Boton>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
