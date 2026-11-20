import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { registrarNegocio } from "../../api/auth"
import { useAuth } from "../../context/auth-context"
import { mensajeDeError } from "../../utils/errores"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

export default function RegistroAdministrador() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [datos, setDatos] = useState({
    negocio: "",
    descripcion: "",
    nombre: "",
    apellido: "",
    correo: "",
    telefono: "",
    contrasena: "",
    confirmar: "",
  })
  const [errores, setErrores] = useState({})
  const [errorGeneral, setErrorGeneral] = useState("")
  const [enviando, setEnviando] = useState(false)

  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.value })

  const registrar = async (e) => {
    e.preventDefault()
    if (enviando) return

    const nuevos = {}
    if (!contrasenaValida(datos.contrasena)) nuevos.contrasena = MENSAJE_CONTRASENA
    if (datos.confirmar !== datos.contrasena) nuevos.confirmar = "Las contraseñas no coinciden"
    setErrores(nuevos)
    setErrorGeneral("")
    if (Object.keys(nuevos).length > 0) return

    setEnviando(true)
    const email = datos.correo.trim()

    try {
      await registrarNegocio({
        negocio_nombre: datos.negocio.trim(),
        negocio_descripcion: datos.descripcion.trim(),
        nombre: datos.nombre.trim(),
        apellido: datos.apellido.trim(),
        email,
        telefono: datos.telefono.trim(),
        password: datos.contrasena,
        password_confirmacion: datos.confirmar,
      })
    } catch (err) {
      setErrorGeneral(mensajeDeError(err, "No pudimos registrar tu negocio. Intenta de nuevo."))
      setEnviando(false)
      return
    }

    // El registro no devuelve tokens: la sesión se abre con las mismas credenciales.
    try {
      await login({ email, password: datos.contrasena })
      navigate("/admin/sedes", {
        replace: true,
        state: { mensaje: "¡Tu negocio está listo! Crea tu primera sede para empezar." },
      })
    } catch {
      // El negocio ya existe: reintentar el registro fallaría por correo repetido.
      navigate("/login", {
        replace: true,
        state: { mensaje: "Tu negocio fue creado. Inicia sesión para continuar." },
      })
    }
  }

  return (
    <AuthLayout amplio volverA="/login">
      <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-white">
        Registra tu negocio
      </h1>

      <form onSubmit={registrar} className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-2">
        <CampoTexto fondo="oscuro" etiqueta="Nombre del negocio*" placeholder="Escribe aquí" maxLength={150} value={datos.negocio} onChange={cambiar("negocio")} required />
        <CampoTexto fondo="oscuro" etiqueta="Descripción del negocio" placeholder="Escribe aquí" value={datos.descripcion} onChange={cambiar("descripcion")} />
        <CampoTexto fondo="oscuro" etiqueta="Tu nombre*" placeholder="Escribe aquí" value={datos.nombre} onChange={cambiar("nombre")} required />
        <CampoTexto fondo="oscuro" etiqueta="Tu apellido*" placeholder="Escribe aquí" value={datos.apellido} onChange={cambiar("apellido")} required />
        <CampoTexto fondo="oscuro" etiqueta="Correo electrónico*" type="email" placeholder="Escribe aquí" value={datos.correo} onChange={cambiar("correo")} required />
        <CampoTexto fondo="oscuro" etiqueta="Teléfono*" type="tel" maxLength={20} placeholder="Escribe aquí" value={datos.telefono} onChange={cambiar("telefono")} required />
        <CampoTexto fondo="oscuro" etiqueta="Contraseña*" type="password" placeholder="Escribe aquí" value={datos.contrasena} error={errores.contrasena} onChange={cambiar("contrasena")} required />
        <CampoTexto fondo="oscuro" etiqueta="Confirmar contraseña*" type="password" placeholder="Escribe aquí" value={datos.confirmar} error={errores.confirmar} onChange={cambiar("confirmar")} required />
        {errorGeneral && (
          <MensajeAlerta tipo="error" className="md:col-span-2">
            {errorGeneral}
          </MensajeAlerta>
        )}
        <Boton type="submit" tipo="ambar" className="mt-3 min-w-[200px] justify-self-center md:col-span-2" disabled={enviando}>
          {enviando ? "Creando negocio…" : "Registrar negocio"}
        </Boton>
      </form>

      <Link to="/login" className="mt-auto pt-8 text-center text-sm text-white underline">
        Ya tengo cuenta
      </Link>
    </AuthLayout>
  )
}
