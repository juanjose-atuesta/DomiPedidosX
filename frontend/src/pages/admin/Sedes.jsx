import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { desactivarSede, listarSedes, reactivarSede } from "../../api/sedes"
import { mensajeDeError } from "../../utils/errores"
import { resumenHorarios } from "../../utils/horarios"

const COLUMNAS = "grid grid-cols-[1fr_1.2fr_1.3fr_0.7fr_290px] items-center gap-4"
const TITULOS = ["Nombre", "Dirección", "Horario", "Estado", "Acciones"]

export default function Sedes() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sedes, setSedes] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState(location.state?.mensaje ?? "")
  const [sedeADesactivar, setSedeADesactivar] = useState(null)
  const [sedeAReactivar, setSedeAReactivar] = useState(null)
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let vigente = true

    listarSedes(true)
      .then((datos) => {
        if (vigente) setSedes(datos)
      })
      .catch((err) => {
        if (vigente) {
          setError(mensajeDeError(err, "No se pudieron cargar las sedes."))
        }
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const cerrar = () => {
    if (procesando) return
    setSedeADesactivar(null)
    setSedeAReactivar(null)
  }

  const confirmarDesactivar = async () => {
    if (!sedeADesactivar || procesando) return

    setProcesando(true)
    setError("")
    setMensaje("")

    try {
      await desactivarSede(sedeADesactivar.id)
      setSedes((actuales) =>
        actuales.map((sede) =>
          sede.id === sedeADesactivar.id ? { ...sede, activa: false } : sede,
        ),
      )
      setMensaje("Sede desactivada correctamente.")
      setSedeADesactivar(null)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo desactivar la sede."))
      setSedeADesactivar(null)
    } finally {
      setProcesando(false)
    }
  }

  const confirmarReactivar = async () => {
    if (!sedeAReactivar || procesando) return

    setProcesando(true)
    setError("")
    setMensaje("")

    try {
      await reactivarSede(sedeAReactivar.id)
      setSedes((actuales) =>
        actuales.map((sede) =>
          sede.id === sedeAReactivar.id ? { ...sede, activa: true } : sede,
        ),
      )
      setMensaje("Sede reactivada correctamente.")
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo reactivar la sede."))
    } finally {
      setSedeAReactivar(null)
      setProcesando(false)
    }
  }

  return (
    <AdminLayout
      titulo="Sedes"
      accion={<Boton onClick={() => navigate("/admin/sedes/nueva")}>Nueva sede</Boton>}
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {cargando ? (
        <MensajeAlerta tipo="info">Cargando sedes…</MensajeAlerta>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
          <div className="min-w-[900px]">
            <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
              {TITULOS.map((titulo) => (
                <p key={titulo}>{titulo}</p>
              ))}
            </div>

            {sedes.length === 0 ? (
              <p className="py-4 text-sm text-texto-sec">No hay sedes registradas.</p>
            ) : (
              sedes.map((sede) => (
                <div
                  key={sede.id}
                  className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}
                >
                  <p>{sede.nombre}</p>
                  <p>{sede.direccion}</p>
                  <p className="line-clamp-2">{resumenHorarios(sede.horarios)}</p>
                  <p className={sede.activa ? "text-exito" : "text-texto-sec"}>
                    {sede.activa ? "Activa" : "Inactiva"}
                  </p>
                  <div className="flex items-center gap-2">
                    <Boton
                      tipo="secundario"
                      onClick={() => navigate(`/admin/sedes/${sede.id}/editar`)}
                    >
                      Editar
                    </Boton>
                    {sede.activa ? (
                      <Boton
                        tipo="secundario"
                        onClick={() => setSedeADesactivar(sede)}
                      >
                        Desactivar
                      </Boton>
                    ) : (
                      <Boton
                        tipo="secundario"
                        onClick={() => setSedeAReactivar(sede)}
                      >
                        Reactivar
                      </Boton>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <ModalConfirmacion
        abierto={Boolean(sedeADesactivar)}
        titulo="¿Desactivar sede?"
        texto="La sede dejará de recibir pedidos nuevos. Los pedidos en curso se terminan normalmente y su historial se conserva."
        textoConfirmar={procesando ? "Desactivando…" : "Desactivar"}
        onConfirmar={confirmarDesactivar}
        onCancelar={cerrar}
      />

      <ModalConfirmacion
        abierto={Boolean(sedeAReactivar)}
        titulo="¿Reactivar sede?"
        texto="La sede volverá a estar visible para los clientes y podrá recibir pedidos nuevos."
        textoConfirmar={procesando ? "Reactivando…" : "Reactivar"}
        onConfirmar={confirmarReactivar}
        onCancelar={cerrar}
      />
    </AdminLayout>
  )
}
