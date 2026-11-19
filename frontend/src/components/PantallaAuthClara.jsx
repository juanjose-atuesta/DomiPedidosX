import AuthLayout from "../layouts/AuthLayout"
import { fondoCrema, iconoBolsaRoja } from "../assets"

// Marco de las pantallas de cuenta sobre fondo claro (recuperar, activar).
// `children` recibe la clase de espaciado según el tamaño de pantalla.
export default function PantallaAuthClara({ titulo, volverA = "/login", children }) {
  return (
    <>
      <div className="lg:hidden">
        <AuthLayout variante="claro" volverA={volverA}>
          <h1 className="mt-6 text-center font-titulo text-[28px] font-semibold leading-9 text-primario">
            {titulo}
          </h1>
          {children("mt-8 gap-5")}
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
            {titulo}
          </h1>
          <div className="mt-10 w-full max-w-[400px]">{children("gap-7")}</div>
        </div>
      </main>
    </>
  )
}
