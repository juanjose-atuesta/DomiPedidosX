import Boton from "../components/Boton"
import { useAuth } from "../context/auth-context"

// Destino de un rol sin panel propio: nunca deja la cuenta sin salida.
export default function PanelNoDisponible() {
  const { logout } = useAuth()

  return (
    <main className="flex min-h-screen items-center justify-center bg-fondo p-6">
      <section className="flex w-full max-w-[480px] flex-col items-center gap-4 rounded-2xl border border-borde bg-white p-8 text-center">
        <h1 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
          Panel no disponible
        </h1>
        <p className="text-base text-texto-sec">
          Tu cuenta todavía no tiene un panel disponible. Cierra sesión o consulta con el
          administrador de tu negocio.
        </p>
        <Boton onClick={logout}>Cerrar sesión</Boton>
      </section>
    </main>
  )
}
