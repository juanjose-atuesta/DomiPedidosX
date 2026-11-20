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
        <Boton tipo="contornoClaro" className="min-w-[200px]" onClick={() => navigate("/login")}>
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
      <section className="flex flex-col items-center bg-fondo px-10 pt-[24vh]">
        <h1 className="font-titulo text-[40px] font-bold leading-[48px] text-primario">
          Regístrate o Ingresa
        </h1>
        <div className="mt-[10vh] flex w-fit flex-col gap-[6vh]">
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
            onClick={() => navigate("/login")}
          >
            Ya tengo cuenta
          </Boton>
        </div>
      </section>

      <section className="relative flex flex-col overflow-hidden bg-primario px-8">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: fondoRojo ? `url(${fondoRojo})` : undefined }}
        />
        {logoBlanco && (
          <img
            src={logoBlanco}
            alt="DomiPedidosX"
            className="relative z-10 mt-4 h-[170px] w-[170px] self-center object-contain"
          />
        )}
        <p className="relative z-10 my-auto font-titulo text-[clamp(2.5rem,4.4vw,4rem)] font-bold leading-[1.2] text-white">
          Antójate.
          <br />
          Nosotros lo llevamos.
        </p>
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