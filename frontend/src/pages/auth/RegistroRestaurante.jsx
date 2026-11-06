import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import { fondoRojo } from "../../assets"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

const TIPOS_COCINA = ["Hamburguesas", "Pizza", "Pastas", "Pollo", "Comida rápida", "Postres", "Otro"]
const CIUDADES = ["Cali", "Jamundí", "Palmira", "Yumbo"]

export default function RegistroRestaurante() {
  const navigate = useNavigate()
  const [contrasena, setContrasena] = useState("")
  const [error, setError] = useState("")

  const registrar = (e) => {
    e.preventDefault()
    if (!contrasenaValida(contrasena)) {
      setError(MENSAJE_CONTRASENA)
      return
    }
    navigate("/iniciar-sesion")
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-primario">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: fondoRojo ? `url(${fondoRojo})` : undefined }}
      />

      <main className="relative z-10 mx-auto grid min-h-screen max-w-[1280px] items-center gap-10 px-6 py-10 lg:grid-cols-2 lg:px-12">
        <section className="text-white">
          <h1 className="font-titulo text-3xl font-semibold leading-tight lg:text-[32px]">
            ¡Regístrate en DomiPedidosX!
          </h1>
          <p className="mt-6 max-w-[480px] font-titulo text-xl font-semibold leading-snug lg:text-[28px]">
            Es el momento perfecto para expandir tu negocio.
          </p>
        </section>

        <form
          onSubmit={registrar}
          className="mx-auto w-full max-w-[562px] rounded-3xl bg-fondo p-8 shadow-xl"
        >
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-primario">
            Registra tu restaurante
          </h2>
          <p className="mt-1 text-sm text-primario">
            ¿Ya tienes una cuenta?{" "}
            <Link to="/iniciar-sesion" className="font-semibold underline">
              Haz clic aquí
            </Link>
          </p>

          <div className="mt-6 grid grid-cols-12 gap-4">
            <CampoTexto
              className="col-span-12 sm:col-span-6"
              etiqueta="Nombre del restaurante"
              placeholder="Escribe aquí"
              required
            />
            <CampoSelect
              className="col-span-12 sm:col-span-6"
              etiqueta="Tipo de cocina"
              opciones={TIPOS_COCINA}
            />
            <CampoSelect className="col-span-12" etiqueta="Ciudad" opciones={CIUDADES} />
            <CampoTexto
              className="col-span-12"
              etiqueta="Dirección del restaurante"
              placeholder="Escribe aquí"
              required
            />
            <CampoTexto
              className="col-span-12 sm:col-span-5"
              etiqueta="NIT"
              inputMode="numeric"
              placeholder="Escribe aquí"
              required
            />
            <CampoTexto
              className="col-span-12 sm:col-span-7"
              etiqueta="Teléfono de contacto"
              type="tel"
              placeholder="Escribe aquí"
              required
            />
            <CampoTexto
              className="col-span-12"
              etiqueta="Correo electrónico de contacto"
              type="email"
              placeholder="Escribe aquí"
              required
            />
            <CampoTexto
              className="col-span-12"
              etiqueta="Contraseña"
              type="password"
              placeholder="Escribe aquí"
              value={contrasena}
              error={error}
              onChange={(e) => {
                setContrasena(e.target.value)
                setError("")
              }}
              required
            />
          </div>

          <Boton type="submit" anchoCompleto className="mt-6">
            Registrar restaurante
          </Boton>
        </form>
      </main>
    </div>
  )
}