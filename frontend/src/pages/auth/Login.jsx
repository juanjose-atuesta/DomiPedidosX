import { useState } from "react"
import { Link, Navigate, useLocation } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { fondoRojo, fondoVino } from "../../assets"
import { useAuth } from "../../context/auth-context"
import { puedeEntrarA, rutaInicio } from "../../utils/roles"

export default function Login() {
  const location = useLocation()
  const { usuario, cargando, login } = useAuth()
  const [identificador, setIdentificador] = useState("")
  const [contrasena, setContrasena] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  const ingresar = async (e) => {
    e.preventDefault()
    setError("")
    setEnviando(true)

    try {
      // Al abrirse la sesión, el bloque de abajo lleva al usuario a su destino.
      await login({
        email: identificador.trim(),
        password: contrasena,
      })
    } catch (err) {
      const detalle = err.response?.data?.detail
      setError(detalle || "No pudimos iniciar sesión. Verifica tus datos e intenta de nuevo.")
    } finally {
      setEnviando(false)
    }
  }

  const cambiarIdentificador = (e) => {
    setIdentificador(e.target.value)
    setError("")
  }

  const cambiarContrasena = (e) => {
    setContrasena(e.target.value)
    setError("")
  }

  if (cargando) {
    return <p className="p-8 text-texto">Cargando…</p>
  }

  // `/` y las rutas desconocidas llegan aquí: quien ya tiene sesión sigue a su panel.
  if (usuario) {
    const desde = location.state?.desde?.pathname
    const destino = desde && puedeEntrarA(usuario.rol, desde) ? desde : rutaInicio(usuario.rol)
    return <Navigate to={destino} replace />
  }

  const imagenFondo = fondoVino ?? fondoRojo
  const mensajes = (
    <>
      {location.state?.mensaje && !error && (
        <MensajeAlerta tipo="info">{location.state.mensaje}</MensajeAlerta>
      )}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
    </>
  )

  return (
    <>
      <div className="lg:hidden">
        <AuthLayout volverA="/bienvenida">
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
            {mensajes}
            <Boton
              type="submit"
              tipo="ambar"
              className="min-w-[200px] self-center"
              disabled={enviando}
            >
              {enviando ? "Ingresando…" : "Iniciar Sesión"}
            </Boton>
          </form>

          <div className="mt-auto flex flex-col gap-3 pt-8 text-center text-sm text-white">
            <Link to="/recuperar-contrasena" className="underline">
              Olvidé mi contraseña
            </Link>
            <Link to="/registro" className="underline">
              Crear una cuenta
            </Link>
            <Link to="/registro-administrador" className="font-semibold underline">
              ¿Tienes un negocio? Regístrate como Administrador aquí
            </Link>
          </div>
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

            {mensajes}

            <Boton type="submit" anchoCompleto className="mt-2" disabled={enviando}>
              {enviando ? "Ingresando…" : "Iniciar sesión"}
            </Boton>

            <div className="flex flex-col items-center gap-4">
              <Link to="/recuperar-contrasena" className="font-titulo font-medium text-texto underline">
                Olvidé mi contraseña
              </Link>
              <Link to="/registro" className="font-titulo font-medium text-texto">
                Crear una cuenta
              </Link>
              <Link to="/registro-administrador" className="text-center font-titulo font-medium text-texto">
                ¿Tienes un negocio? Regístrate como Administrador aquí
              </Link>
            </div>
          </form>
        </div>
      </main>
    </>
  )
}
