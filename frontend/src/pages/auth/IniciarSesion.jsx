import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"

export default function IniciarSesion() {
  const navigate = useNavigate()
  const [identificador, setIdentificador] = useState("")
  const [contrasena, setContrasena] = useState("")
  const [error, setError] = useState("")

  const ingresar = (e) => {
    e.preventDefault()
    if (contrasena.length < 8) {
      setError("Correo o contraseña incorrectos")
      return
    }
    navigate("/cliente")
  }

  return (
    <AuthLayout volverA="/login">
      <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-white">
        ¡Estás de vuelta!
      </h1>

      <form onSubmit={ingresar} className="mt-12 flex flex-col gap-6">
        <CampoTexto
          fondo="oscuro"
          etiqueta="Correo o Teléfono"
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
        {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
        <Boton type="submit" tipo="ambar" className="min-w-[200px] self-center">
          Iniciar Sesión
        </Boton>
      </form>

      <Link to="/recuperar-contrasena" className="mt-auto pt-8 text-center text-sm text-white underline">
        Olvidé mi contraseña
      </Link>
    </AuthLayout>
  )
}