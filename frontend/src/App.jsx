import { useState } from "react"
import Boton from "./components/Boton"
import CampoTexto from "./components/CampoTexto"
import Interruptor from "./components/Interruptor"
import EtiquetaEstado from "./components/EtiquetaEstado"

export default function App() {
  const [activo, setActivo] = useState(true)

  return (
    <div className="space-y-8 p-8">
      <div className="flex max-w-sm flex-col gap-4">
        <CampoTexto etiqueta="Nombre completo" placeholder="Escribe aquí" />
        <CampoTexto etiqueta="Correo electrónico" placeholder="Escribe aquí" error="Correo no válido" />
        <CampoTexto etiqueta="Correo" defaultValue="laura@correo.com" disabled />
      </div>

      <div className="flex max-w-sm flex-col gap-4 bg-vino p-6">
        <CampoTexto fondo="oscuro" etiqueta="Correo o teléfono" placeholder="Escribe aquí" error="Credenciales incorrectas" />
        <Boton tipo="ambar" anchoCompleto>Iniciar sesión</Boton>
      </div>

      <div className="flex items-center gap-3">
        <Interruptor activo={activo} onChange={setActivo} etiqueta="Disponible" />
        <Interruptor activo={false} />
      </div>

      <div className="flex flex-wrap gap-2">
        <EtiquetaEstado estado="recibido" />
        <EtiquetaEstado estado="preparacion" />
        <EtiquetaEstado estado="listo" />
        <EtiquetaEstado estado="camino" />
        <EtiquetaEstado estado="entregado" />
        <EtiquetaEstado estado="cancelado" />
      </div>
    </div>
  )
}