import { useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import PantallaAuthClara from "../../components/PantallaAuthClara"
import { confirmarRecuperacion, solicitarRecuperacion } from "../../api/auth"
import { mensajeDeError } from "../../utils/errores"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

// Paso 1: pide el correo y el backend envía el enlace (no revela si existe).
function SolicitarEnlace({ className }) {
  const [email, setEmail] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [respuesta, setRespuesta] = useState("")
  const [error, setError] = useState("")

  const enviar = async (e) => {
    e.preventDefault()
    if (enviando) return
    setEnviando(true)
    setError("")
    try {
      const datos = await solicitarRecuperacion(email.trim())
      setRespuesta(datos.mensaje)
    } catch (err) {
      setError(mensajeDeError(err, "No pudimos enviar el enlace. Intenta de nuevo."))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className={`flex flex-col ${className}`}>
      <p className="text-sm text-texto-sec">
        Escribe el correo de tu cuenta y te enviaremos un enlace para elegir una nueva contraseña.
      </p>
      <CampoTexto
        etiqueta="Correo electrónico"
        type="email"
        placeholder="Escribe aquí"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {respuesta ? (
        <MensajeAlerta tipo="exito">{respuesta}</MensajeAlerta>
      ) : (
        <Boton type="submit" anchoCompleto className="min-w-[200px]" disabled={enviando}>
          {enviando ? "Enviando…" : "Enviar enlace"}
        </Boton>
      )}
    </form>
  )
}

// Paso 2: llega desde el enlace del correo (?uid=…&token=…).
function NuevaContrasena({ uidb64, token, className }) {
  const navigate = useNavigate()
  const [nueva, setNueva] = useState("")
  const [confirmar, setConfirmar] = useState("")
  const [errores, setErrores] = useState({})
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [listo, setListo] = useState(false)

  const guardar = async (e) => {
    e.preventDefault()
    const nuevos = {}
    if (!contrasenaValida(nueva)) nuevos.nueva = MENSAJE_CONTRASENA
    if (confirmar !== nueva) nuevos.confirmar = "Las contraseñas no coinciden"
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0 || enviando) return

    setEnviando(true)
    setError("")
    try {
      await confirmarRecuperacion({ uidb64, token, nuevaContrasena: nueva })
      setListo(true)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo cambiar la contraseña."))
    } finally {
      setEnviando(false)
    }
  }

  if (listo) {
    return (
      <div className={`flex flex-col ${className}`}>
        <MensajeAlerta tipo="exito">Contraseña actualizada. Ya puedes iniciar sesión.</MensajeAlerta>
        <Boton anchoCompleto className="min-w-[200px]" onClick={() => navigate("/login")}>
          Ir a iniciar sesión
        </Boton>
      </div>
    )
  }

  return (
    <form onSubmit={guardar} className={`flex flex-col ${className}`}>
      <CampoTexto
        etiqueta="Nueva contraseña"
        type="password"
        placeholder="Escribe aquí"
        value={nueva}
        error={errores.nueva}
        onChange={(e) => setNueva(e.target.value)}
        required
      />
      <CampoTexto
        etiqueta="Confirmar contraseña"
        type="password"
        placeholder="Escribe aquí"
        value={confirmar}
        error={errores.confirmar}
        onChange={(e) => setConfirmar(e.target.value)}
        required
      />
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      <Boton type="submit" anchoCompleto className="min-w-[200px]" disabled={enviando}>
        {enviando ? "Guardando…" : "Restablecer contraseña"}
      </Boton>
    </form>
  )
}

export default function RecuperarContrasena() {
  const [parametros] = useSearchParams()
  const uidb64 = parametros.get("uid")
  const token = parametros.get("token")

  return (
    <PantallaAuthClara titulo="Recuperar contraseña">
      {(className) =>
        uidb64 && token ? (
          <NuevaContrasena uidb64={uidb64} token={token} className={className} />
        ) : (
          <SolicitarEnlace className={className} />
        )
      }
    </PantallaAuthClara>
  )
}
