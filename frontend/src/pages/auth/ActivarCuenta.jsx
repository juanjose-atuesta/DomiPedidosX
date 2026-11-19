import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import PantallaAuthClara from "../../components/PantallaAuthClara"
import { activarCuenta, consultarActivacion } from "../../api/auth"
import { mensajeDeError } from "../../utils/errores"
import { etiquetaRol } from "../../utils/roles"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

// El personal nuevo llega aquí desde el correo y define su propia contraseña.
function Formulario({ token, className }) {
  const navigate = useNavigate()
  const [cuenta, setCuenta] = useState(null)
  const [estado, setEstado] = useState("cargando")
  const [password, setPassword] = useState("")
  const [confirmacion, setConfirmacion] = useState("")
  const [errores, setErrores] = useState({})
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let vigente = true
    consultarActivacion(token)
      .then((datos) => {
        if (!vigente) return
        setCuenta(datos)
        setEstado("listo")
      })
      .catch((err) => {
        if (!vigente) return
        setError(mensajeDeError(err, "El enlace de activación no es válido."))
        setEstado("invalido")
      })
    return () => {
      vigente = false
    }
  }, [token])

  const guardar = async (e) => {
    e.preventDefault()
    const nuevos = {}
    if (!contrasenaValida(password)) nuevos.password = MENSAJE_CONTRASENA
    if (confirmacion !== password) nuevos.confirmacion = "Las contraseñas no coinciden"
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0 || enviando) return

    setEnviando(true)
    setError("")
    try {
      await activarCuenta({ token, password, passwordConfirmacion: confirmacion })
      setEstado("activada")
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo activar la cuenta."))
    } finally {
      setEnviando(false)
    }
  }

  if (estado === "cargando") {
    return <p className="text-center text-sm text-texto-sec">Verificando enlace…</p>
  }

  if (estado === "invalido" || estado === "activada") {
    return (
      <div className={`flex flex-col ${className}`}>
        {estado === "activada" ? (
          <MensajeAlerta tipo="exito">Cuenta activada. Ya puedes iniciar sesión.</MensajeAlerta>
        ) : (
          <MensajeAlerta tipo="error">
            {error} Pide al administrador de tu negocio que te envíe un enlace nuevo.
          </MensajeAlerta>
        )}
        <Boton anchoCompleto onClick={() => navigate("/login")}>
          Ir a iniciar sesión
        </Boton>
      </div>
    )
  }

  return (
    <form onSubmit={guardar} className={`flex flex-col ${className}`}>
      <p className="text-sm text-texto-sec">
        Hola {cuenta.nombre}, tu cuenta de{" "}
        <strong className="text-texto">{etiquetaRol(cuenta.rol).toLowerCase()}</strong> ({cuenta.email})
        está lista. Elige tu contraseña para empezar.
      </p>
      <CampoTexto
        etiqueta="Contraseña"
        type="password"
        placeholder="Escribe aquí"
        value={password}
        error={errores.password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <CampoTexto
        etiqueta="Confirmar contraseña"
        type="password"
        placeholder="Escribe aquí"
        value={confirmacion}
        error={errores.confirmacion}
        onChange={(e) => setConfirmacion(e.target.value)}
        required
      />
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      <Boton type="submit" anchoCompleto disabled={enviando}>
        {enviando ? "Activando…" : "Activar cuenta"}
      </Boton>
    </form>
  )
}

export default function ActivarCuenta() {
  const { token } = useParams()
  return (
    <PantallaAuthClara titulo="Activa tu cuenta">
      {(className) => <Formulario key={token} token={token} className={className} />}
    </PantallaAuthClara>
  )
}
