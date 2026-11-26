import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import MensajeAlerta from "../../components/MensajeAlerta"
import api from "../../api/cliente"
import { mensajeDeError } from "../../utils/errores"

const DIAS = {
  1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 
  5: "Viernes", 6: "Sábado", 7: "Domingo"
}

export default function Capacidad() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [franjas, setFranjas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")

  // Estados para el formulario de creación (HU-9.1)
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [dia, setDia] = useState(1)
  const [inicio, setInicio] = useState("12:00")
  const [fin, setFin] = useState("13:00")
  const [tope, setTope] = useState(10)
  const [guardando, setGuardando] = useState(false)

  const cargarFranjas = () => {
    setCargando(true)
    api.get(`/cobertura/sedes/${id}/capacidad/`)
      .then((res) => {
        setFranjas(res.data)
        setError("")
      })
      .catch((err) => setError(mensajeDeError(err, "No se pudieron cargar las franjas.")))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargarFranjas()
  }, [id])

  const guardarFranja = async (e) => {
    e.preventDefault()
    setGuardando(true)
    setError("")
    try {
      await api.post(`/cobertura/sedes/${id}/capacidad/`, {
        dia_semana: Number(dia),
        hora_inicio: inicio,
        hora_fin: fin,
        tope_pedidos: Number(tope)
      })
      setMostrarFormulario(false)
      cargarFranjas() // Recargamos la lista
    } catch (err) {
      setError(mensajeDeError(err, "Error al guardar la franja."))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <AdminLayout 
      titulo="Capacidad de la Sede"
      accion={
        <div className="flex gap-2">
          <Boton tipo="secundario" onClick={() => navigate("/admin/sedes")}>
            Volver a Sedes
          </Boton>
          <Boton onClick={() => setMostrarFormulario(!mostrarFormulario)}>
            {mostrarFormulario ? "Cancelar" : "Agregar Franja"}
          </Boton>
        </div>
      }
    >
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      
      {/* Formulario para crear nueva franja (HU-9.1) */}
      {mostrarFormulario && (
        <div className="rounded-xl border border-borde bg-white p-6 max-w-3xl mb-6">
          <h2 className="font-titulo text-lg font-semibold mb-4">Nueva franja horaria</h2>
          <form onSubmit={guardarFranja} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <label className="flex flex-col text-sm">
                Día
                <select value={dia} onChange={e => setDia(e.target.value)} className="border p-2 rounded mt-1">
                  {Object.entries(DIAS).map(([num, nombre]) => (
                    <option key={num} value={num}>{nombre}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col text-sm">
                Hora inicio
                <input type="time" value={inicio} onChange={e => setInicio(e.target.value)} className="border p-2 rounded mt-1" required />
              </label>
              <label className="flex flex-col text-sm">
                Hora fin
                <input type="time" value={fin} onChange={e => setFin(e.target.value)} className="border p-2 rounded mt-1" required />
              </label>
              <label className="flex flex-col text-sm">
                Tope pedidos
                <input type="number" min="1" value={tope} onChange={e => setTope(e.target.value)} className="border p-2 rounded mt-1" required />
              </label>
            </div>
            <Boton type="submit" disabled={guardando} className="w-fit">
              {guardando ? "Guardando..." : "Guardar Franja"}
            </Boton>
          </form>
        </div>
      )}

      {/* Lista de franjas y alertas (HU-9.4) */}
      <div className="rounded-xl border border-borde bg-white p-6 max-w-3xl">
        <h2 className="font-titulo text-xl font-semibold text-texto mb-2">
          Topes de pedidos simultáneos
        </h2>
        <p className="text-sm text-texto-sec mb-6">
          Define cuántos pedidos puede atender la cocina al mismo tiempo en cada franja horaria para no saturarse.
        </p>

        {cargando ? (
          <p className="text-sm text-texto-sec">Cargando franjas horarias...</p>
        ) : franjas.length === 0 ? (
          <p className="text-sm text-texto-sec">Esta sede aún no tiene franjas de capacidad configuradas.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {franjas.map((franja) => {
              const pedidosActuales = franja.pedidos_actuales || 0;
              const porcentajeOcupacion = (pedidosActuales / franja.tope_pedidos) * 100;
              const cercaDelLimite = porcentajeOcupacion >= 80;

              return (
                <div key={franja.id} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border border-borde p-4 rounded-lg">
                  <div>
                    <p className="font-semibold text-texto">
                      {DIAS[franja.dia_semana] || `Día ${franja.dia_semana}`}: {franja.hora_inicio} - {franja.hora_fin}
                    </p>
                    <p className="text-sm text-texto-sec mt-1">
                      Tope configurado: <strong>{franja.tope_pedidos} pedidos simultáneos</strong>
                    </p>
                  </div>

                  <div className={`px-4 py-2 rounded-lg text-sm font-semibold ${cercaDelLimite ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {cercaDelLimite 
                      ? "⚠️ Cerca del límite de capacidad" 
                      : `Ocupación actual: ${pedidosActuales} / ${franja.tope_pedidos}`}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
