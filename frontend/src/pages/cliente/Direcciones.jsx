import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { Lapiz, Papelera } from "../../components/Iconos"
import { eliminarDireccion, listarDirecciones } from "../../api/direcciones"
import { mensajeDeError } from "../../utils/errores"

export default function Direcciones() {
  const navigate = useNavigate()
  const [direcciones, setDirecciones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [aEliminar, setAEliminar] = useState(null)
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let vigente = true

    listarDirecciones()
      .then((datos) => {
        if (vigente) setDirecciones(datos)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar tus direcciones."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const eliminar = async () => {
    if (!aEliminar || procesando) return
    setProcesando(true)
    setError("")
    try {
      await eliminarDireccion(aEliminar.id)
      setDirecciones((ds) => ds.filter((d) => d.id !== aEliminar.id))
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo eliminar la dirección."))
    } finally {
      setAEliminar(null)
      setProcesando(false)
    }
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
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {cargando && <p className="text-center text-sm text-texto-sec">Cargando direcciones…</p>}
      {!cargando && !error && direcciones.length === 0 && (
        <p className="text-center text-sm text-texto-sec">Aún no tienes direcciones guardadas</p>
      )}

      <ul className="flex flex-col gap-[38px]">
        {direcciones.map((d) => (
          <li key={d.id} className="flex items-center gap-[18px]">
            <div className="flex min-h-20 min-w-0 flex-1 flex-col justify-center rounded-xl border border-ambar bg-white px-4 py-2">
              <p className="text-sm text-[#1d1b20]">
                {d.alias}
                {d.es_principal && " · Principal"}
              </p>
              <p className="text-base font-semibold text-[#1d1b20]">{d.direccion_texto}</p>
              {d.detalles && <p className="text-xs text-texto-sec">{d.detalles}</p>}
            </div>
            <div className="flex flex-col gap-4 text-ambar">
              <button
                type="button"
                aria-label={`Editar ${d.alias}`}
                onClick={() => navigate(`/cliente/direcciones/${d.id}/editar`)}
              >
                <Lapiz />
              </button>
              <button type="button" aria-label={`Eliminar ${d.alias}`} onClick={() => setAEliminar(d)}>
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
        textoConfirmar={procesando ? "Eliminando…" : "Eliminar"}
        onConfirmar={eliminar}
        onCancelar={() => {
          if (!procesando) setAEliminar(null)
        }}
      />
    </ClienteLayout>
  )
}
