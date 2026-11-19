import { useEffect, useRef, useState } from "react"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { Candado } from "../../components/Iconos"
import { fondoPerfil, iconoBolsaNaranja } from "../../assets"
import { desactivarMiCuenta } from "../../api/auth"
import { useAuth } from "../../context/auth-context"
import { mensajeDeError } from "../../utils/errores"

const FONDO = {
  backgroundImage: `${fondoPerfil ? `url(${fondoPerfil}), ` : ""}linear-gradient(to bottom, #ffffff, #fce3c8)`,
  backgroundSize: "100% 100%",
  backgroundPosition: "top center",
  backgroundAttachment: "fixed",
}

export default function Perfil() {
  const { usuario, actualizarPerfil, logout } = useAuth()
  const entradaFoto = useRef(null)
  const [foto, setFoto] = useState(null)
  const [nombre, setNombre] = useState(usuario?.nombre ?? "")
  const [apellido, setApellido] = useState(usuario?.apellido ?? "")
  const [telefono, setTelefono] = useState(usuario?.telefono ?? "")
  const [eliminando, setEliminando] = useState(false)
  const [claveDesactivar, setClaveDesactivar] = useState("")
  const [errorDesactivar, setErrorDesactivar] = useState("")
  const [desactivando, setDesactivando] = useState(false)
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    return () => {
      if (foto) URL.revokeObjectURL(foto)
    }
  }, [foto])

  const elegirFoto = (archivo) => {
    if (!archivo || !archivo.type.startsWith("image/")) return
    setFoto(URL.createObjectURL(archivo))
  }

  const guardar = async (e) => {
    e.preventDefault()
    setMensaje(null)
    setGuardando(true)
    try {
      await actualizarPerfil({ nombre, apellido, telefono })
      setMensaje({ tipo: "exito", texto: "Datos actualizados correctamente" })
    } catch {
      setMensaje({ tipo: "error", texto: "No pudimos guardar los cambios. Intenta de nuevo." })
    } finally {
      setGuardando(false)
    }
  }

  const cerrarDesactivar = () => {
    if (desactivando) return
    setEliminando(false)
    setClaveDesactivar("")
    setErrorDesactivar("")
  }

  const desactivar = async () => {
    if (desactivando) return
    if (!claveDesactivar) {
      setErrorDesactivar("Escribe tu contraseña para confirmar")
      return
    }
    setDesactivando(true)
    setErrorDesactivar("")
    try {
      await desactivarMiCuenta(claveDesactivar)
      logout()
    } catch (err) {
      setErrorDesactivar(mensajeDeError(err, "No pudimos desactivar tu cuenta."))
      setDesactivando(false)
    }
  }

  return (
    <ClienteLayout
      titulo="Mi perfil"
      barra
      fondo={FONDO}
      derecha={
        iconoBolsaNaranja && (
          <img src={iconoBolsaNaranja} alt="DomiPedidosX" className="h-[38px] w-[38px] object-cover" />
        )
      }
    >
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-32 w-32 items-center justify-center overflow-hidden rounded-full bg-fondo font-titulo text-[56px] font-semibold text-ambar">
          {foto ? (
            <img src={foto} alt="Tu foto de perfil" className="h-full w-full object-cover" />
          ) : (
            nombre.charAt(0).toUpperCase() || "?"
          )}
        </div>
        <Boton tipo="ambar" pequeno onClick={() => entradaFoto.current?.click()}>
          Editar imagen
        </Boton>
        <input
          ref={entradaFoto}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => elegirFoto(e.target.files[0])}
        />
      </div>

      <form onSubmit={guardar} className="flex flex-col gap-4">
        <CampoTexto
          etiqueta="Nombre*"
          placeholder="Escribe aquí"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <CampoTexto
          etiqueta="Apellido*"
          placeholder="Escribe aquí"
          value={apellido}
          onChange={(e) => setApellido(e.target.value)}
          required
        />
        <div className="relative">
          <CampoTexto
            etiqueta="Correo electrónico*"
            value={usuario?.email ?? ""}
            disabled
            readOnly
          />
          <Candado className="absolute bottom-[14px] right-4 h-5 w-5 text-texto-sec" />
        </div>
        <CampoTexto
          etiqueta="Teléfono móvil*"
          type="tel"
          placeholder="Escribe aquí"
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
          required
        />
        {mensaje && <MensajeAlerta tipo={mensaje.tipo}>{mensaje.texto}</MensajeAlerta>}
        <Boton type="submit" tipo="ambar" className="w-[249px] self-center" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar cambios"}
        </Boton>
      </form>

      <div className="flex flex-col items-center gap-4 pb-4">
        <Boton tipo="secundario" onClick={logout}>
          Cerrar sesión
        </Boton>
        <button
          type="button"
          onClick={() => setEliminando(true)}
          className="text-base font-semibold text-primario hover:underline"
        >
          Desactivar cuenta
        </button>
      </div>


      <ModalConfirmacion
        abierto={eliminando}
        titulo="¿Desactivar tu cuenta?"
        texto="No podrás volver a iniciar sesión. Tus pedidos en curso se entregarán normalmente y tu historial se conserva."
        textoConfirmar={desactivando ? "Desactivando…" : "Desactivar cuenta"}
        onConfirmar={desactivar}
        onCancelar={cerrarDesactivar}
      >
        <CampoTexto
          etiqueta="Confirma con tu contraseña"
          type="password"
          value={claveDesactivar}
          error={errorDesactivar}
          onChange={(e) => setClaveDesactivar(e.target.value)}
          autoComplete="current-password"
        />
      </ModalConfirmacion>
    </ClienteLayout>
  )
}