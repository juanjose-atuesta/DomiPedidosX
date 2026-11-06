import { useState } from "react"
import { useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

export default function RecuperarContrasena() {
  const navigate = useNavigate()
  const [correo, setCorreo] = useState("")
  const [nueva, setNueva] = useState("")
  const [confirmar, setConfirmar] = useState("")
  const [errores, setErrores] = useState({})
  const [listo, setListo] = useState(false)

  const guardar = (e) => {
    e.preventDefault()
    const nuevos = {}
    if (!contrasenaValida(nueva)) nuevos.nueva = MENSAJE_CONTRASENA
    if (confirmar !== nueva) nuevos.confirmar = "Las contraseñas no coinciden"
    setErrores(nuevos)
    setListo(Object.keys(nuevos).length === 0)
  }

  return (
    <AuthLayout variante="claro" volverA="/iniciar-sesion">
      <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-primario">
        Recuperar contraseña
      </h1>

      <form onSubmit={guardar} className="mt-8 flex flex-col gap-5">
        <CampoTexto
          etiqueta="Correo electrónico"
          type="email"
          placeholder="Escribe aquí"
          value={correo}
          onChange={(e) => setCorreo(e.target.value)}
          required
        />
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

        {listo ? (
          <>
            <MensajeAlerta tipo="exito">Contraseña actualizada. Ya puedes iniciar sesión.</MensajeAlerta>
            <Boton className="min-w-[200px] self-center" onClick={() => navigate("/iniciar-sesion")}>
              Ir a iniciar sesión
            </Boton>
          </>
        ) : (
          <Boton type="submit" className="min-w-[200px] self-center">
            Restablecer contraseña
          </Boton>
        )}
      </form>
    </AuthLayout>
  )
}