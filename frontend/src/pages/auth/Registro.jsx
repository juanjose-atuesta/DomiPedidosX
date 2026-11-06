import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { registrarCliente } from "../../api/auth"
import { useAuth } from "../../context/auth-context"
import { mensajeDeError } from "../../utils/errores"
import { rutaInicio } from "../../utils/roles"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

export default function Registro() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [datos, setDatos] = useState({
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
      await registrarCliente({
        nombre: datos.nombre.trim(),
        apellido: datos.apellido.trim(),
        email,
        telefono: datos.telefono.trim(),
        password: datos.contrasena,
        password_confirmacion: datos.confirmar,
      })
    } catch (err) {
      setErrorGeneral(mensajeDeError(err, "No pudimos crear tu cuenta. Intenta de nuevo."))
      setEnviando(false)
      return
    }

    // El registro no devuelve tokens: la sesión se abre con las mismas credenciales.
    try {
      const perfil = await login({ email, password: datos.contrasena })
      navigate(rutaInicio(perfil.rol), { replace: true })
    } catch {
      // La cuenta ya existe: reintentar el registro fallaría por correo repetido.
      navigate("/iniciar-sesion", {
        replace: true,
        state: { mensaje: "Tu cuenta fue creada. Inicia sesión para continuar." },
      })
    }
  }

  return (
    <AuthLayout volverA="/login">
      <form onSubmit={registrar} className="mt-8 flex flex-col gap-5">
        <CampoTexto fondo="oscuro" etiqueta="Nombre*" placeholder="Escribe aquí" value={datos.nombre} onChange={cambiar("nombre")} required />
        <CampoTexto fondo="oscuro" etiqueta="Apellido*" placeholder="Escribe aquí" value={datos.apellido} onChange={cambiar("apellido")} required />
        <CampoTexto fondo="oscuro" etiqueta="Correo Electrónico*" type="email" placeholder="Escribe aquí" value={datos.correo} onChange={cambiar("correo")} required />
        <CampoTexto fondo="oscuro" etiqueta="Teléfono*" type="tel" maxLength={20} placeholder="Escribe aquí" value={datos.telefono} onChange={cambiar("telefono")} required />
        <CampoTexto fondo="oscuro" etiqueta="Contraseña*" type="password" placeholder="Escribe aquí" value={datos.contrasena} error={errores.contrasena} onChange={cambiar("contrasena")} required />
        <CampoTexto fondo="oscuro" etiqueta="Confirmar Contraseña*" type="password" placeholder="Escribe aquí" value={datos.confirmar} error={errores.confirmar} onChange={cambiar("confirmar")} required />
        {errorGeneral && <MensajeAlerta tipo="error">{errorGeneral}</MensajeAlerta>}
        <Boton type="submit" tipo="ambar" className="mt-3 min-w-[200px] self-center" disabled={enviando}>
          {enviando ? "Creando cuenta…" : "Registrarme"}
        </Boton>
      </form>

      <Link to="/iniciar-sesion" className="mt-auto pt-8 text-center text-sm text-white underline">
        Ya tengo cuenta
      </Link>
    </AuthLayout>
  )
}
