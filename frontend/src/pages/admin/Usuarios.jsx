import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { useAuth } from "../../context/auth-context"
import {
  cambiarRolUsuario,
  desactivarUsuario,
  listarUsuarios,
} from "../../api/usuarios"
import { mensajeDeError } from "../../utils/errores"
import { etiquetaRol, OPCIONES_ROL } from "../../utils/roles"

const COLUMNAS = "grid grid-cols-[1fr_1.2fr_0.9fr_1fr_290px] items-center gap-4"
const TITULOS = ["Nombre", "Correo", "Rol", "Sedes", "Acciones"]

function nombreCompleto(usuario) {
  return [usuario.nombre, usuario.apellido].filter(Boolean).join(" ")
}

export default function Usuarios() {
  const navigate = useNavigate()
  const location = useLocation()
  const { usuario: usuarioActual } = useAuth()
  const [usuarios, setUsuarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState(location.state?.mensaje ?? "")
  const [modal, setModal] = useState(null)
  const [nuevoRol, setNuevoRol] = useState("")
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let vigente = true

    listarUsuarios()
      .then((datos) => {
        if (vigente) setUsuarios(datos)
      })
      .catch((err) => {
        if (vigente) {
          setError(mensajeDeError(err, "No se pudieron cargar los usuarios."))
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
    if (!procesando) setModal(null)
  }

  const abrirCambioRol = (usuario) => {
    setNuevoRol(usuario.rol)
    setModal({ tipo: "rol", usuario })
  }

  const confirmarCambioRol = async () => {
    if (!modal?.usuario || procesando) return

    if (nuevoRol === modal.usuario.rol) {
      setModal(null)
      return
    }

    setProcesando(true)
    setError("")
    setMensaje("")

    try {
      await cambiarRolUsuario(modal.usuario.id, nuevoRol)
      setUsuarios((actuales) =>
        actuales.map((usuario) =>
          usuario.id === modal.usuario.id
            ? { ...usuario, rol: nuevoRol }
            : usuario,
        ),
      )
      setMensaje(`Rol de ${nombreCompleto(modal.usuario)} actualizado.`)
      setModal(null)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo cambiar el rol del usuario."))
      setModal(null)
    } finally {
      setProcesando(false)
    }
  }

  const confirmarDesactivar = async () => {
    if (!modal?.usuario || procesando) return

    setProcesando(true)
    setError("")
    setMensaje("")

    try {
      await desactivarUsuario(modal.usuario.id)
      setUsuarios((actuales) =>
        actuales.filter((usuario) => usuario.id !== modal.usuario.id),
      )
      setMensaje(`${nombreCompleto(modal.usuario)} fue desactivado.`)
      setModal(null)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo desactivar la cuenta."))
      setModal(null)
    } finally {
      setProcesando(false)
    }
  }

  return (
    <AdminLayout
      titulo="Usuarios"
      accion={
        <Boton onClick={() => navigate("/admin/usuarios/nueva")}>
          Crear cuenta de personal
        </Boton>
      }
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {cargando ? (
        <MensajeAlerta tipo="info">Cargando usuarios…</MensajeAlerta>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
          <div className="min-w-[900px]">
            <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
              {TITULOS.map((titulo) => (
                <p key={titulo}>{titulo}</p>
              ))}
            </div>

            {usuarios.length === 0 ? (
              <p className="py-4 text-sm text-texto-sec">
                No hay usuarios activos.
              </p>
            ) : (
              usuarios.map((usuario) => {
                const esUsuarioActual = usuario.id === usuarioActual?.id

                return (
                  <div
                    key={usuario.id}
                    className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}
                  >
                    <p>
                      {nombreCompleto(usuario)}
                      {esUsuarioActual && (
                        <span className="ml-2 text-xs text-texto-sec">
                          (tú)
                        </span>
                      )}
                    </p>
                    <p>{usuario.email}</p>
                    <p>{etiquetaRol(usuario.rol)}</p>
                    <p>
                      {usuario.sedes?.length
                        ? usuario.sedes.map((sede) => sede.nombre).join(", ")
                        : "—"}
                    </p>
                    <div className="flex items-center gap-2">
                      {esUsuarioActual ? (
                        <p className="text-sm text-texto-sec">Tu cuenta</p>
                      ) : (
                        <>
                          <Boton
                            tipo="secundario"
                            onClick={() => abrirCambioRol(usuario)}
                          >
                            Cambiar rol
                          </Boton>
                          <Boton
                            tipo="secundario"
                            onClick={() =>
                              setModal({ tipo: "desactivar", usuario })
                            }
                          >
                            Desactivar
                          </Boton>
                        </>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      <ModalConfirmacion
        abierto={modal?.tipo === "desactivar"}
        titulo="¿Desactivar cuenta?"
        texto={`${nombreCompleto(modal?.usuario ?? {})} ya no podrá iniciar sesión. Su historial y sus pedidos en curso se conservan.`}
        textoConfirmar={procesando ? "Desactivando…" : "Desactivar"}
        onConfirmar={confirmarDesactivar}
        onCancelar={cerrar}
      />

      <ModalConfirmacion
        abierto={modal?.tipo === "rol"}
        titulo="Cambiar rol"
        texto="El nuevo rol se aplicará en el próximo inicio de sesión de la persona."
        textoConfirmar={procesando ? "Guardando…" : "Guardar rol"}
        onConfirmar={confirmarCambioRol}
        onCancelar={cerrar}
      >
        <CampoSelect
          etiqueta="Nuevo rol"
          opciones={OPCIONES_ROL}
          value={nuevoRol}
          onChange={(evento) => setNuevoRol(evento.target.value)}
          placeholder="Seleccionar rol"
        />
      </ModalConfirmacion>
    </AdminLayout>
  )
}
