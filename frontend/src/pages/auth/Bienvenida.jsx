import { useNavigate } from "react-router-dom"
import AuthLayout from "../../layouts/AuthLayout"
import Boton from "../../components/Boton"

export default function Bienvenida() {
  const navigate = useNavigate()

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