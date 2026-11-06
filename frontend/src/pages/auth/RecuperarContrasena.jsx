import { useState } from "react"
import { useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { fondoCrema, iconoBolsaRoja } from "../../assets"
import { MENSAJE_CONTRASENA, contrasenaValida } from "../../utils/validaciones"

function FormularioRecuperar({ className = "" }) {
  const navigate = useNavigate()
  const [identificador, setIdentificador] = useState("")
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
    <form onSubmit={guardar} className={`flex flex-col ${className}`}>
      <CampoTexto
        etiqueta="Correo electrónico"
        type="email"
        placeholder="Escribe aquí"
        value={identificador}
        onChange={(e) => setIdentificador(e.target.value)}
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
          <Boton anchoCompleto className="min-w-[200px]" onClick={() => navigate("/login")}>
            Ir a iniciar sesión
          </Boton>
        </>
      ) : (
        <Boton type="submit" anchoCompleto className="min-w-[200px]">
          Restablecer contraseña
        </Boton>
      )}
    </form>
  )
}

export default function RecuperarContrasena() {
  return (
    <>
      <div className="lg:hidden">
        <AuthLayout variante="claro" volverA="/login">
          <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-primario">
            Recuperar contraseña
          </h1>
          <FormularioRecuperar className="mt-8 gap-5" />
        </AuthLayout>
      </div>

      <main className="relative hidden min-h-screen overflow-hidden bg-fondo lg:block">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: fondoCrema ? `url(${fondoCrema})` : undefined }}
        />
        <div className="relative z-10 mx-auto flex w-full max-w-[640px] flex-col items-center px-6 pb-16 pt-10">
          {iconoBolsaRoja && (
            <img src={iconoBolsaRoja} alt="DomiPedidosX" className="h-14 w-14 object-contain" />
          )}
          <h1 className="mt-10 text-center font-texto text-[clamp(2.5rem,4vw,3.5rem)] font-bold leading-tight text-primario">
            Recuperar contraseña
          </h1>
          <div className="mt-10 w-full max-w-[400px]">
            <FormularioRecuperar className="gap-7" />
          </div>
        </div>
      </main>
    </>
  )
}