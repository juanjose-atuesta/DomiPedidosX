import BarraLateral from "../components/BarraLateral"

export default function AdminLayout({ titulo, accion, children }) {
  return (
    <div className="flex min-h-screen bg-fondo">
      <BarraLateral />
      <main className="flex min-w-0 flex-1 flex-col gap-6 p-8">
        <div className="flex items-start justify-between gap-4">
          <h1 className="font-titulo text-[40px] font-bold leading-[48px] text-texto">
            {titulo}
          </h1>
          {accion}
        </div>
        {children}
      </main>
    </div>
  )
}