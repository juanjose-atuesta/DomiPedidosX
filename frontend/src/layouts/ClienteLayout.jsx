import { useNavigate } from "react-router-dom"
import { FlechaIzquierda } from "../components/Iconos"
import BarraInferior from "../components/BarraInferior"

export default function ClienteLayout({
  titulo,
  volverA,
  derecha,
  pie,
  barra = false,
  fondo,
  children,
}) {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen justify-center bg-fondo" style={fondo}>
      <div className="flex min-h-screen w-full max-w-[430px] flex-col px-[22px] pb-[38px] pt-16">
        <header className="flex items-center justify-between pl-1">
          <button
            type="button"
            onClick={() => (volverA ? navigate(volverA) : navigate(-1))}
            className="flex items-center gap-[3px] text-base font-semibold text-black"
          >
            <FlechaIzquierda />
            {titulo}
          </button>
          {derecha}
        </header>
        <main className={`mt-[60px] flex flex-1 flex-col gap-5 ${barra ? "pb-24" : ""}`}>
          {children}
        </main>
        {pie && <footer className="pt-8">{pie}</footer>}
      </div>
      {barra && <BarraInferior />}
    </div>
  )
}