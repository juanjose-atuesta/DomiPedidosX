import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { fondoRojo, fondoVino } from "../../assets"

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

  const cambiarIdentificador = (e) => {
    setIdentificador(e.target.value)
    setError("")
  }

  const cambiarContrasena = (e) => {
    setContrasena(e.target.value)
    setError("")
  }

  const imagenFondo = fondoVino ?? fondoRojo

  return (
    <>
      <div className="lg:hidden">
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
              onChange={cambiarIdentificador}
              required
            />
            <CampoTexto
              fondo="oscuro"
              etiqueta="Contraseña"
              type="password"
              placeholder="Escribe aquí"
              value={contrasena}
              onChange={cambiarContrasena}
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
      </div>

      <main className="relative hidden min-h-screen overflow-hidden bg-vino lg:block">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: imagenFondo ? `url(${imagenFondo})` : undefined }}
        />
        {!fondoVino && <div aria-hidden="true" className="absolute inset-0 bg-vino/70" />}

        <div className="relative z-10 mx-auto grid min-h-screen w-full max-w-[1280px] grid-cols-2 items-center gap-12 px-12 py-10">
          <h1 className="text-center font-texto text-[clamp(2.5rem,4.4vw,4rem)] font-semibold leading-[1.25] text-white">
            ¡Bienvenido a
            <br />
            DomiPedidosX!
          </h1>

          <form
            onSubmit={ingresar}
            className="flex w-full max-w-[520px] flex-col gap-6 justify-self-center rounded-[40px] bg-fondo px-10 py-12"
          >
            <h2 className="text-center font-titulo text-[40px] font-bold leading-[48px] text-texto">
              Inicio de Sesión
            </h2>

            <CampoTexto
              etiqueta="Correo electrónico*"
              type="email"
              placeholder="Escribe aquí"
              value={identificador}
              onChange={cambiarIdentificador}
              required
            />
            <CampoTexto
              etiqueta="Contraseña*"
              type="password"
              placeholder="Escribe aquí"
              value={contrasena}
              onChange={cambiarContrasena}
              required
            />

            {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

            <Boton type="submit" anchoCompleto className="mt-2">
              Iniciar sesión
            </Boton>

            <div className="flex flex-col items-center gap-4">
              <Link to="/recuperar-contrasena" className="font-titulo font-medium text-texto underline">
                Olvidé mi contraseña
              </Link>
              <Link to="/registro" className="font-titulo font-medium text-texto">
                Crear una cuenta
              </Link>
            </div>
          </form>
        </div>
      </main>
    </>
  )
}