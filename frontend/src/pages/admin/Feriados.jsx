import { useEffect, useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { crearFeriado, eliminarFeriado, listarFeriados, listarSedes } from "../../api/sedes"
import { mensajeDeError } from "../../utils/errores"
import { fechaDeHoy, formatearFecha } from "../../utils/formato"

// Días en que una, varias o todas las sedes del negocio no reciben pedidos (HU-8.9).
export default function Feriados() {
  const [feriados, setFeriados] = useState([])
  const [sedes, setSedes] = useState([])
  const [cargando, setCargando] = useState(true)
  const [fecha, setFecha] = useState(fechaDeHoy)
  const [nombre, setNombre] = useState("")
  const [elegidas, setElegidas] = useState([])
  const [aEliminar, setAEliminar] = useState(null)
  const [procesando, setProcesando] = useState(false)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState("")

  useEffect(() => {
    let vigente = true
    Promise.all([listarFeriados(fechaDeHoy()), listarSedes()])
      .then(([datosFeriados, datosSedes]) => {
        if (!vigente) return
        setFeriados(datosFeriados)
        setSedes(datosSedes)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar los feriados."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [])

  const alternarSede = (id) =>
    setElegidas((actuales) =>
      actuales.includes(id) ? actuales.filter((s) => s !== id) : [...actuales, id],
    )

  const guardar = async (e) => {
    e.preventDefault()
    if (procesando || !nombre.trim()) return
    setProcesando(true)
    setError("")
    setMensaje("")
    try {
      const nuevo = await crearFeriado({ fecha, nombre: nombre.trim(), sedes_ids: elegidas })
      setFeriados((actuales) =>
        [...actuales, nuevo].sort((a, b) => a.fecha.localeCompare(b.fecha)),
      )
      setNombre("")
      setElegidas([])
      setMensaje(`Feriado "${nuevo.nombre}" agregado.`)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar el feriado."))
    } finally {
      setProcesando(false)
    }
  }

  const confirmarEliminar = async () => {
    if (!aEliminar || procesando) return
    setProcesando(true)
    try {
      await eliminarFeriado(aEliminar.id)
      setFeriados((actuales) => actuales.filter((f) => f.id !== aEliminar.id))
      setMensaje(`Feriado "${aEliminar.nombre}" eliminado.`)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo eliminar el feriado."))
    } finally {
      setAEliminar(null)
      setProcesando(false)
    }
  }

  return (
    <AdminLayout titulo="Feriados">
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_1.2fr]">
        <form onSubmit={guardar} className="flex flex-col gap-4 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-xl font-semibold text-texto">Nuevo feriado</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto etiqueta="Fecha" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
            <CampoTexto
              etiqueta="Nombre"
              placeholder="Navidad"
              maxLength={100}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
          </div>
          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm text-texto">Sedes que cierran</legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {sedes.map((sede) => (
                <label
                  key={sede.id}
                  className="flex items-center gap-2 rounded-lg border border-borde px-3 py-2 text-sm text-texto"
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-primario"
                    checked={elegidas.includes(sede.id)}
                    onChange={() => alternarSede(sede.id)}
                  />
                  {sede.nombre}
                </label>
              ))}
            </div>
            <p className="text-xs text-texto-sec">
              {elegidas.length === 0
                ? "Sin sedes marcadas, el feriado cierra todas las sedes del negocio."
                : `Cierra ${elegidas.length} de ${sedes.length} sedes.`}
            </p>
          </fieldset>
          <Boton type="submit" className="self-end" disabled={procesando || !nombre.trim()}>
            {procesando ? "Guardando…" : "Agregar feriado"}
          </Boton>
        </form>

        <section className="flex flex-col gap-2 rounded-xl border border-borde bg-white p-4">
          <h2 className="font-titulo text-xl font-semibold text-texto">Próximos feriados</h2>
          {cargando && <p className="text-sm text-texto-sec">Cargando…</p>}
          {!cargando && feriados.length === 0 && (
            <p className="text-sm text-texto-sec">No hay feriados programados.</p>
          )}
          {feriados.map((feriado) => (
            <div
              key={feriado.id}
              className="flex items-center justify-between gap-3 border-b border-borde py-2 last:border-0"
            >
              <div className="min-w-0 text-sm">
                <p className="font-semibold text-texto">
                  {formatearFecha(feriado.fecha)} · {feriado.nombre}
                </p>
                <p className="text-xs text-texto-sec">
                  {feriado.aplica_a_todas
                    ? "Todas las sedes"
                    : feriado.sedes.map((s) => s.nombre).join(", ")}
                </p>
              </div>
              <Boton tipo="texto" pequeno onClick={() => setAEliminar(feriado)}>
                Eliminar
              </Boton>
            </div>
          ))}
        </section>
      </div>

      <ModalConfirmacion
        abierto={Boolean(aEliminar)}
        titulo="¿Eliminar feriado?"
        texto="Las sedes volverán a recibir pedidos ese día según su horario."
        textoConfirmar={procesando ? "Eliminando…" : "Eliminar"}
        onConfirmar={confirmarEliminar}
        onCancelar={() => setAEliminar(null)}
      />
    </AdminLayout>
  )
}
