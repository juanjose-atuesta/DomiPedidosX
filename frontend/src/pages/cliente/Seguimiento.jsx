import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import MapaDireccion from "../../components/MapaDireccion"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import { API_URL } from "../../api/cliente"

export default function Seguimiento() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [pedido, setPedido] = useState(null)

  return (
    <ClienteLayout titulo="Seguimiento" volverA="/cliente/pedidos">
      <div className="flex flex-col items-center justify-center py-10">
        <p className="text-texto-sec">Cargando seguimiento del pedido #{id}...</p>
      </div>
    </ClienteLayout>
  )
}
