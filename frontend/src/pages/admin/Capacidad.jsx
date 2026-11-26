import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import api from "../../api/cliente" // Axios configurado

export default function Capacidad() {
  const { id } = useParams()
  const [franjas, setFranjas] = useState([])
  
  useEffect(() => {
    api.get(`/cobertura/sedes/${id}/capacidad/`).then(res => setFranjas(res.data))
  }, [id])

  return (
    <AdminLayout titulo="Capacidad de la Sede">
      <div className="bg-white p-4 rounded border">
        <h2 className="font-bold mb-4">Topes de pedidos por franja</h2>
        {franjas.length === 0 ? <p>No hay franjas configuradas.</p> : (
          franjas.map(f => <p key={f.id}>{f.dia_semana} {f.hora_inicio}-{f.hora_fin}: {f.tope_pedidos} pedidos</p>)
        )}
      </div>
    </AdminLayout>
  )
}
