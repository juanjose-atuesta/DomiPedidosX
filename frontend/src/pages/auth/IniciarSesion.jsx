import { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { useAuth } from "../../context/auth-context"
import { rutaInicio } from "../../utils/roles"

export default function IniciarSesion() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [identificador, setIdentificador] = useState("")
  const [contrasena, setContrasena] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  const ingresar = async (e) => {
    e.preventDefault()
    setError("")
    setEnviando(true)

    try {
      const perfil = await login({
        email: identificador.trim(),
        password: contrasena,
      })
      const desde = location.state?.desde?.pathname
      navigate(desde ?? rutaInicio(perfil.rol), { replace: true })
    } catch (err) {
      const detalle = err.response?.data?.detail
      setError(detalle || "No pudimos iniciar sesión. Verifica tus datos e intenta de nuevo.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <AuthLayout volverA="/login">
      <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-white">
        ¡Estás de vuelta!
      </h1>

      <form onSubmit={ingresar} className="mt-12 flex flex-col gap-6">
        <CampoTexto
          fondo="oscuro"
          etiqueta="Correo electrónico"
          type="email"
          placeholder="Escribe aquí"
          value={identificador}
          onChange={(e) => {
            setIdentificador(e.target.value)
            setError("")
          }}
          required
        />
        <CampoTexto
          fondo="oscuro"
          etiqueta="Contraseña"
          type="password"
          placeholder="Escribe aquí"
          value={contrasena}
          onChange={(e) => {
            setContrasena(e.target.value)
            setError("")
          }}
          required
        />
        {location.state?.mensaje && !error && (
          <MensajeAlerta tipo="info">{location.state.mensaje}</MensajeAlerta>
        )}
        {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
        <Boton
          type="submit"
          tipo="ambar"
          className="min-w-[200px] self-center"
          disabled={enviando}
        >
          {enviando ? "Ingresando…" : "Iniciar Sesión"}
        </Boton>
      </form>

      <Link to="/recuperar-contrasena" className="mt-auto pt-8 text-center text-sm text-white underline">
        Olvidé mi contraseña
      </Link>
    </AuthLayout>
  )
}