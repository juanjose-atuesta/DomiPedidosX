import { useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"
import { fondoRojo, logoBlanco } from "../../assets"

function VersionCelular({ navigate }) {
  return (
    <AuthLayout logoGrande>
      <p className="mt-2 text-center text-base font-semibold text-fondo">
        Antójate. Nosotros lo llevamos.
      </p>

      <div className="mt-24 flex flex-col items-center gap-4">
        <Boton tipo="ambar" className="min-w-[200px]" onClick={() => navigate("/registro")}>
          Registrarme
        </Boton>
        <Boton tipo="contornoClaro" className="min-w-[200px]" onClick={() => navigate("/iniciar-sesion")}>
          Ya tengo cuenta
        </Boton>
      </div>

      <p className="mt-auto pt-10 text-center text-base text-fondo">
        Al continuar aceptas los Términos y la Política de Privacidad
      </p>
    </AuthLayout>
  )
}

function VersionEscritorio({ navigate }) {
  return (
    <main className="grid min-h-screen grid-cols-[minmax(480px,45%)_1fr]">
      <section className="flex flex-col items-center justify-center bg-fondo px-10">
        <h1 className="font-titulo text-[40px] font-bold leading-[48px] text-primario">
          Regístrate o Ingresa
        </h1>
        <div className="mt-12 flex w-fit flex-col gap-8">
          <Boton anchoCompleto className="min-w-[300px]" onClick={() => navigate("/registro")}>
            Continuar con Correo Electrónico
          </Boton>
          <Boton anchoCompleto className="min-w-[300px]" onClick={() => navigate("/registro")}>
            Continuar con Teléfono
          </Boton>
          <Boton
            tipo="secundario"
            anchoCompleto
            className="min-w-[300px]"
            onClick={() => navigate("/iniciar-sesion")}
          >
            Ya tengo cuenta
          </Boton>
        </div>
      </section>

      <section className="relative flex flex-col justify-center overflow-hidden bg-primario px-16">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: fondoRojo ? `url(${fondoRojo})` : undefined }}
        />
        <div className="relative z-10 flex flex-col items-start gap-8">
          {logoBlanco && (
            <img src={logoBlanco} alt="DomiPedidosX" className="h-[170px] w-[170px] object-contain" />
          )}
          <p className="max-w-[640px] font-titulo text-6xl font-bold leading-tight text-white">
            Antójate. Nosotros lo llevamos.
          </p>
        </div>
      </section>
    </main>
  )
}

export default function Bienvenida() {
  const navigate = useNavigate()

  return (
    <>
      <div className="lg:hidden">
        <VersionCelular navigate={navigate} />
      </div>
      <div className="hidden lg:block">
        <VersionEscritorio navigate={navigate} />
      </div>
    </>
  )
}