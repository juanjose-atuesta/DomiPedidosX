import Boton from "./Boton"

export default function TarjetaProducto({
  nombre,
  descripcion,
  tiempo,
  precio,
  imagen,
  agotado = false,
  onAgregar,
}) {
  return (
    <article className="flex h-full w-full max-w-[280px] flex-col overflow-hidden rounded-xl border border-borde bg-white">
      <div className={`h-40 shrink-0 bg-borde ${agotado ? "opacity-50" : ""}`}>
        {imagen && <img src={imagen} alt={nombre} className="h-full w-full object-cover" />}
      </div>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex flex-col gap-1">
          <h3 className="line-clamp-1 font-titulo text-xl font-semibold text-texto">{nombre}</h3>
          <p className="line-clamp-2 min-h-10 text-sm text-texto-sec">{descripcion}</p>
          <p className="text-xs text-texto-sec">⏱ {tiempo} min</p>
        </div>
        <div className="mt-auto flex items-center justify-between">
          <span className="font-titulo text-xl font-semibold text-acento">
            ${precio.toLocaleString("es-CO")}
          </span>
          <Boton disabled={agotado} onClick={onAgregar}>
            {agotado ? "Agotado" : "Agregar"}
          </Boton>
        </div>
      </div>
    </article>
  )
}