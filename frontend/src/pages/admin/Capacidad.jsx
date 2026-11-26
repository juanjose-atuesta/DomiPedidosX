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

  useEffect(() => {
    let vigente = true

    api.get(`/cobertura/sedes/${id}/capacidad/`)
      .then((res) => {
        if (vigente) {
          setFranjas(res.data)
          setError("")
        }
      })
      .catch((err) => {
        if (vigente) {
          setError(mensajeDeError(err, "No se pudieron cargar las franjas de capacidad."))
        }
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => { vigente = false }
  }, [id])

  return (
    <AdminLayout 
      titulo="Capacidad de la Sede"
      accion={
        <Boton tipo="secundario" onClick={() => navigate("/admin/sedes")}>
          Volver a Sedes
        </Boton>
      }
    >
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      
      <div className="rounded-xl border border-borde bg-white p-6 max-w-3xl">
        <h2 className="font-titulo text-xl font-semibold text-texto mb-2">
          Topes de pedidos simultáneos (HU-9.1)
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
              // Lógica de la alerta (HU-9.4): Si los pedidos actuales superan el 80% del tope
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

                  {/* Alerta Visual (HU-9.4) */}
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
