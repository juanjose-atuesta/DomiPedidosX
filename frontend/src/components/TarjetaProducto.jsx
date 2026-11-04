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
    <article className="w-full max-w-[280px] overflow-hidden rounded-xl border border-borde bg-white">
      <div className={`h-40 bg-borde ${agotado ? "opacity-50" : ""}`}>
        {imagen && <img src={imagen} alt={nombre} className="h-full w-full object-cover" />}
      </div>
      <div className="flex flex-col gap-3 p-4">
        <div className="flex flex-col gap-1">
          <h3 className="font-titulo text-xl font-semibold text-texto">{nombre}</h3>
          <p className="text-sm text-texto-sec">{descripcion}</p>
          <p className="text-xs text-texto-sec">⏱ {tiempo} min</p>
        </div>
        <div className="flex items-center justify-between">
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