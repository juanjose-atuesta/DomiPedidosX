import { useNavigate } from "react-router-dom"
import Boton from "../components/Boton"
import { useAuth } from "../context/auth-context"

export default function AccesoDenegado() {
  const navigate = useNavigate()
  const { usuario, logout } = useAuth()

  return (
    <main className="flex min-h-screen items-center justify-center bg-fondo p-6">
      <section
        role="alert"
        className="flex w-full max-w-[480px] flex-col items-center gap-4 rounded-2xl border border-borde bg-white p-8 text-center"
      >
        <span
          aria-hidden="true"
          className="flex h-14 w-14 items-center justify-center rounded-full bg-error text-3xl text-white"
        >
          ✕
        </span>
        <h1 className="font-titulo text-[28px] font-semibold leading-9 text-texto">Acceso denegado</h1>
        <p className="text-base text-texto-sec">No tienes permiso para ver esta sección.</p>
        <div className="flex flex-wrap justify-center gap-3">
          <Boton onClick={() => navigate("/")}>Volver al inicio</Boton>
          {usuario && (
            <Boton tipo="secundario" onClick={logout}>
              Cerrar sesión
            </Boton>
          )}
        </div>
      </section>
    </main>
  )
}