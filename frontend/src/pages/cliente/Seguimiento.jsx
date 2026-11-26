import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import MapaDireccion from "../../components/MapaDireccion"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import { obtenerPedido } from "../../api/pedidos" // Asegúrate de que esta función exista, si no, usa axios
import { ETIQUETA_ESTADO } from "../../utils/pedidos"

export default function Seguimiento() {
  const { id } = useParams()
  const [pedido, setPedido] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    const cargarPedido = async () => {
      try {
        // Si no existe obtenerPedido, usa: const { data } = await api.get(`/pedidos/${id}/`)
        const datos = await obtenerPedido(id) 
        setPedido(datos)
        setError("")
      } catch (err) {
        setError("No se pudo cargar el pedido")
      }
    }

    cargarPedido()
    const intervalo = setInterval(cargarPedido, 10000) // Cada 10 segundos
    return () => clearInterval(intervalo)
  }, [id])

  if (error) return <ClienteLayout titulo="Seguimiento"><p className="text-red-500 p-4">{error}</p></ClienteLayout>
  if (!pedido) return <ClienteLayout titulo="Seguimiento"><p className="p-4 text-center">Cargando mapa...</p></ClienteLayout>

  const posicionRepartidor = pedido.repartidor_lat && pedido.repartidor_lng 
    ? [pedido.repartidor_lat, pedido.repartidor_lng] 
    : [3.4516, -76.5320] // Coordenadas por defecto si falla

  return (
    <ClienteLayout titulo={`Pedido #${pedido.id}`} volverA="/cliente/pedidos">
      <div className="flex flex-col gap-4 p-4">
        <div className="flex justify-between items-center">
          <span className="font-semibold">Estado actual</span>
          <EtiquetaEstado estado={ETIQUETA_ESTADO[pedido.estado]} />
        </div>
        
        {pedido.estado === "en_camino" && (
          <div>
            <p className="text-sm mb-2 font-semibold">Ubicación del repartidor:</p>
            {/* Usamos el mapa para mostrar el puntito */}
            <MapaDireccion posicion={posicionRepartidor} />
          </div>
        )}
        
        <div className="bg-white p-4 rounded-xl border border-borde">
          <p className="text-sm text-gray-600">Tiempo estimado de entrega: <strong>{pedido.tiempo_estimado_entrega} min</strong></p>
          <p className="text-sm mt-2">Dirección: {pedido.direccion_entrega}</p>
        </div>
      </div>
    </ClienteLayout>
  )
}
