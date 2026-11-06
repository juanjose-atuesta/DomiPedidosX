import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import ModalAviso from "../../components/ModalAviso"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

const CORREO_YA_REGISTRADO = "juan123@gmail.com"

export default function Registro() {
  const navigate = useNavigate()
  const [datos, setDatos] = useState({
    nombre: "",
    correo: "",
    telefono: "",
    contrasena: "",
    confirmar: "",
  })
  const [errores, setErrores] = useState({})
  const [correoRepetido, setCorreoRepetido] = useState(false)

  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.value })

  const registrar = (e) => {
    e.preventDefault()
    const nuevos = {}
    if (!contrasenaValida(datos.contrasena)) nuevos.contrasena = MENSAJE_CONTRASENA
    if (datos.confirmar !== datos.contrasena) nuevos.confirmar = "Las contraseñas no coinciden"
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) return

    if (datos.correo.trim().toLowerCase() === CORREO_YA_REGISTRADO) {
      setCorreoRepetido(true)
      return
    }
    navigate("/iniciar-sesion")
  }

  return (
    <AuthLayout volverA="/login">
      <form onSubmit={registrar} className="mt-8 flex flex-col gap-5">
        <CampoTexto fondo="oscuro" etiqueta="Nombre*" placeholder="Escribe aquí" value={datos.nombre} onChange={cambiar("nombre")} required />
        <CampoTexto fondo="oscuro" etiqueta="Correo Electrónico*" type="email" placeholder="Escribe aquí" value={datos.correo} onChange={cambiar("correo")} required />
        <CampoTexto fondo="oscuro" etiqueta="Teléfono*" type="tel" placeholder="Escribe aquí" value={datos.telefono} onChange={cambiar("telefono")} required />
        <CampoTexto fondo="oscuro" etiqueta="Contraseña*" type="password" placeholder="Escribe aquí" value={datos.contrasena} error={errores.contrasena} onChange={cambiar("contrasena")} required />
        <CampoTexto fondo="oscuro" etiqueta="Confirmar Contraseña*" type="password" placeholder="Escribe aquí" value={datos.confirmar} error={errores.confirmar} onChange={cambiar("confirmar")} required />
        <Boton type="submit" tipo="ambar" className="mt-3 min-w-[200px] self-center">
          Registrarme
        </Boton>
      </form>

      <Link to="/iniciar-sesion" className="mt-auto pt-8 text-center text-sm text-white underline">
        Ya tengo cuenta
      </Link>

      <ModalAviso
        abierto={correoRepetido}
        conIcono={false}
        titulo="¡Correo ya registrado!"
        onCerrar={() => setCorreoRepetido(false)}
      />
    </AuthLayout>
  )
}