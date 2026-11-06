import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import { actualizarSede, crearSede, obtenerSede } from "../../api/sedes"
import { mensajeDeError } from "../../utils/errores"
import { OPCIONES_DIAS, normalizarHora } from "../../utils/horarios"

const HORARIO_VACIO = {
  dia_semana: "1",
  hora_apertura: "",
  hora_cierre: "",
}

const FORMULARIO_VACIO = {
  nombre: "",
  telefono: "",
  direccion: "",
  latitud: "",
  longitud: "",
}

export default function FormularioSede() {
  const navigate = useNavigate()
  const { id } = useParams()
  const esEdicion = Boolean(id)
  const [sede, setSede] = useState(null)
  const [formulario, setFormulario] = useState(FORMULARIO_VACIO)
  const [horarios, setHorarios] = useState(
    esEdicion ? [] : [{ ...HORARIO_VACIO }],
  )
  const [cargando, setCargando] = useState(esEdicion)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState("")
  const [errorCarga, setErrorCarga] = useState("")

  const volver = () => navigate("/admin/sedes")

  useEffect(() => {
    if (!esEdicion) return

    let vigente = true

    obtenerSede(id)
      .then((datos) => {
        if (!vigente) return

        setSede(datos)
        setFormulario({
          nombre: datos.nombre ?? "",
          telefono: datos.telefono ?? "",
          direccion: datos.direccion ?? "",
          latitud: datos.latitud ?? "",
          longitud: datos.longitud ?? "",
        })
        setHorarios(
          (datos.horarios ?? []).map((horario) => ({
            dia_semana: String(horario.dia_semana),
            hora_apertura: normalizarHora(horario.hora_apertura),
            hora_cierre: normalizarHora(horario.hora_cierre),
          })),
        )
      })
      .catch((err) => {
        if (vigente) {
          setErrorCarga(mensajeDeError(err, "No se pudo cargar la sede."))
        }
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [esEdicion, id])

  const actualizarCampo = (campo) => (evento) => {
    setFormulario((actual) => ({ ...actual, [campo]: evento.target.value }))
  }

  const actualizarHorario = (indice, campo, valor) => {
    setHorarios((actuales) =>
      actuales.map((horario, posicion) =>
        posicion === indice ? { ...horario, [campo]: valor } : horario,
      ),
    )
  }

  const agregarHorario = () => {
    setHorarios((actuales) => [...actuales, { ...HORARIO_VACIO }])
  }

  const eliminarHorario = (indice) => {
    setHorarios((actuales) =>
      actuales.filter((_, posicion) => posicion !== indice),
    )
  }

  const guardar = async (evento) => {
    evento.preventDefault()
    setError("")
    setEnviando(true)

    try {
      const datos = {
        nombre: formulario.nombre.trim(),
        telefono: formulario.telefono.trim(),
        direccion: formulario.direccion.trim(),
        latitud: formulario.latitud === "" ? null : formulario.latitud,
        longitud: formulario.longitud === "" ? null : formulario.longitud,
        horarios: horarios.map((horario) => ({
          dia_semana: Number(horario.dia_semana),
          hora_apertura: horario.hora_apertura,
          hora_cierre: horario.hora_cierre,
        })),
      }

      if (esEdicion) {
        await actualizarSede(id, datos)
      } else {
        await crearSede(datos)
      }

      navigate("/admin/sedes", {
        state: {
          mensaje: esEdicion
            ? "Sede actualizada correctamente."
            : "Sede creada correctamente.",
        },
      })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar la sede."))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <AdminLayout
      titulo={esEdicion ? "Editar sede" : "Nueva sede"}
      accion={
        <Boton tipo="texto" onClick={volver}>
          ← Volver
        </Boton>
      }
    >
      {errorCarga ? (
        <MensajeAlerta tipo="error">{errorCarga}</MensajeAlerta>
      ) : cargando ? (
        <MensajeAlerta tipo="info">Cargando sede…</MensajeAlerta>
      ) : (
        <div className="flex flex-wrap items-start gap-6">
          <form
            onSubmit={guardar}
            className="flex w-full max-w-[704px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <CampoTexto
                etiqueta="Nombre de la sede"
                placeholder="Escribe aquí"
                value={formulario.nombre}
                onChange={actualizarCampo("nombre")}
                required
              />
              <CampoTexto
                etiqueta="Teléfono"
                type="tel"
                placeholder="Escribe aquí"
                value={formulario.telefono}
                onChange={actualizarCampo("telefono")}
                required
              />
              <CampoTexto
                etiqueta="Dirección"
                placeholder="Escribe aquí"
                value={formulario.direccion}
                onChange={actualizarCampo("direccion")}
                className="sm:col-span-2"
                required
              />
              <CampoTexto
                etiqueta="Latitud"
                type="number"
                step="any"
                inputMode="decimal"
                placeholder="Ej. 3.4516"
                value={formulario.latitud}
                onChange={actualizarCampo("latitud")}
              />
              <CampoTexto
                etiqueta="Longitud"
                type="number"
                step="any"
                inputMode="decimal"
                placeholder="Ej. -76.5320"
                value={formulario.longitud}
                onChange={actualizarCampo("longitud")}
              />
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-titulo text-xl font-semibold text-texto">
                    Horarios de atención
                  </h2>
                  <p className="text-sm text-texto-sec">
                    Agrega uno o varios tramos por día.
                  </p>
                </div>
                <Boton tipo="secundario" onClick={agregarHorario}>
                  Agregar horario
                </Boton>
              </div>

              {horarios.length === 0 ? (
                <MensajeAlerta tipo="info">
                  Esta sede no tiene horarios definidos.
                </MensajeAlerta>
              ) : (
                <div className="flex flex-col gap-3">
                  {horarios.map((horario, indice) => (
                    <div
                      key={indice}
                      className="grid items-end gap-3 rounded-lg border border-borde p-3 sm:grid-cols-[1.2fr_1fr_1fr_auto]"
                    >
                      <CampoSelect
                        etiqueta="Día"
                        opciones={OPCIONES_DIAS}
                        value={horario.dia_semana}
                        onChange={(evento) =>
                          actualizarHorario(
                            indice,
                            "dia_semana",
                            evento.target.value,
                          )
                        }
                      />
                      <CampoTexto
                        etiqueta="Apertura"
                        type="time"
                        value={horario.hora_apertura}
                        onChange={(evento) =>
                          actualizarHorario(
                            indice,
                            "hora_apertura",
                            evento.target.value,
                          )
                        }
                        required
                      />
                      <CampoTexto
                        etiqueta="Cierre"
                        type="time"
                        value={horario.hora_cierre}
                        onChange={(evento) =>
                          actualizarHorario(
                            indice,
                            "hora_cierre",
                            evento.target.value,
                          )
                        }
                        required
                      />
                      <Boton
                        tipo="texto"
                        className="mb-0.5"
                        onClick={() => eliminarHorario(indice)}
                        aria-label={`Eliminar horario ${indice + 1}`}
                      >
                        Eliminar
                      </Boton>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <MensajeAlerta tipo="info">
              La sede solo recibirá pedidos dentro de estos horarios.
            </MensajeAlerta>

            {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

            <div className="flex justify-end gap-3 py-[10px]">
              <Boton tipo="secundario" onClick={volver}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={enviando}>
                {enviando ? "Guardando…" : "Guardar sede"}
              </Boton>
            </div>
          </form>

          <aside className="flex w-full max-w-[320px] flex-col items-start gap-3 rounded-xl border border-borde bg-white p-6">
            <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
              Estado de la sede
            </h2>
            {sede && !sede.activa ? (
              <EtiquetaEstado estado="recibido">Inactiva</EtiquetaEstado>
            ) : (
              <EtiquetaEstado estado="entregado">Activa</EtiquetaEstado>
            )}
            <p className="text-base text-texto-sec">
              Podrás desactivarla desde la lista de sedes sin perder su historial
            </p>
          </aside>
        </div>
      )}
    </AdminLayout>
  )
}
