import { useNavigate } from "react-router-dom"
import { FlechaIzquierda } from "../components/Iconos"
import TituloCurvo from "../components/TituloCurvo"
import { fondoCrema, fondoRojo, iconoBolsaRoja, logoBlanco } from "../assets"

export default function AuthLayout({ variante = "oscuro", volverA, logoGrande = false, children }) {
  const navigate = useNavigate()
  const claro = variante === "claro"
  const logo = claro ? iconoBolsaRoja : logoBlanco
  const imagenFondo = claro ? fondoCrema : fondoRojo

  return (
    <div className={claro ? "bg-fondo" : "bg-primario"}>
      <div className="relative mx-auto flex min-h-screen w-full max-w-[430px] flex-col overflow-hidden">
        <div
          aria-hidden="true"
          className={`absolute inset-0 bg-cover bg-center ${claro ? "scale-105 blur-[2px]" : ""}`}
          style={{ backgroundImage: imagenFondo ? `url(${imagenFondo})` : undefined }}
        />

        <div className="relative z-10 flex flex-1 flex-col px-9 pb-10 pt-14">
          {volverA && (
            <button
              type="button"
              onClick={() => navigate(volverA)}
              className={`absolute left-4 top-14 flex items-center gap-[3px] text-base font-semibold ${
                claro ? "text-primario" : "text-fondo"
              }`}
            >
              <FlechaIzquierda />
              Regresar
            </button>
          )}

          <TituloCurvo
            color={claro ? "#9D0208" : "#ffffff"}
            className={`mx-auto w-full max-w-[400px] ${volverA ? "mt-12" : "mt-24"}`}
          />

          {logo && (
            <img
              src={logo}
              alt=""
              className={`mx-auto object-contain ${
                logoGrande ? "-mt-6 h-56 w-56" : "-mt-8 h-[139px] w-[139px]"
              }`}
            />
          )}

          {children}
        </div>
      </div>
    </div>
  )
}