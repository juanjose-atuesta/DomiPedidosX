import { useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { Lapiz, Papelera } from "../../components/Iconos"
import { DIRECCIONES } from "../../data/direcciones"

export default function Direcciones() {
  const navigate = useNavigate()
  const [direcciones, setDirecciones] = useState(DIRECCIONES)
  const [aEliminar, setAEliminar] = useState(null)

  const eliminar = () => {
    setDirecciones((ds) => ds.filter((d) => d.id !== aEliminar.id))
    setAEliminar(null)
  }

  return (
    <ClienteLayout
      titulo="Mis direcciones"
      pie={
        <Boton grande anchoCompleto onClick={() => navigate("/cliente/direcciones/nueva")}>
          Añadir dirección
        </Boton>
      }
    >
      {direcciones.length === 0 && (
        <p className="text-center text-sm text-texto-sec">Aún no tienes direcciones guardadas</p>
      )}

      <ul className="flex flex-col gap-[38px]">
        {direcciones.map((d) => (
          <li key={d.id} className="flex items-center gap-[18px]">
            <div className="flex h-20 flex-1 flex-col justify-center rounded-xl border border-ambar bg-white px-4">
              <p className="text-sm text-[#1d1b20]">{d.nombre}</p>
              <p className="text-base font-semibold text-[#1d1b20]">{d.direccion}</p>
            </div>
            <div className="flex flex-col gap-4 text-ambar">
              <button
                type="button"
                aria-label={`Editar ${d.nombre}`}
                onClick={() => navigate(`/cliente/direcciones/${d.id}/editar`)}
              >
                <Lapiz />
              </button>
              <button type="button" aria-label={`Eliminar ${d.nombre}`} onClick={() => setAEliminar(d)}>
                <Papelera />
              </button>
            </div>
          </li>
        ))}
      </ul>

      <ModalConfirmacion
        abierto={Boolean(aEliminar)}
        titulo="¿Eliminar dirección?"
        texto="Dejará de aparecer en tus direcciones guardadas. Tus pedidos anteriores no se modifican."
        textoConfirmar="Eliminar"
        onConfirmar={eliminar}
        onCancelar={() => setAEliminar(null)}
      />
    </ClienteLayout>
  )
}