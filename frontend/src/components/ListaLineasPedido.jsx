import SelectorCantidad from "./SelectorCantidad"
import { subtotalLinea } from "../utils/carrito"
import { moneda } from "../utils/formato"

export default function ListaLineasPedido({ lineas, onCambiarCantidad, onQuitar }) {
  return (
    <ul className="flex flex-col gap-4">
      {lineas.map((linea) => (
        <li key={linea.clave} className="flex flex-col gap-2 rounded-xl border border-borde bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="font-semibold text-texto">{linea.nombre}</p>
              {linea.opciones.length > 0 && (
                <p className="text-xs text-texto-sec">
                  {linea.opciones.map((o) => o.nombre).join(", ")}
                </p>
              )}
              {linea.notas && <p className="text-xs text-acento">Nota: {linea.notas}</p>}
            </div>
            <span className="shrink-0 font-semibold text-acento">{moneda(subtotalLinea(linea))}</span>
          </div>
          <div className="flex items-center justify-between">
            <SelectorCantidad
              cantidad={linea.cantidad}
              etiqueta={linea.nombre}
              onCambiar={(cantidad) => onCambiarCantidad(linea.clave, cantidad)}
            />
            <button
              type="button"
              aria-label={`Eliminar ${linea.nombre}`}
              onClick={() => onQuitar(linea.clave)}
              className="text-sm font-semibold text-primario underline"
            >
              Eliminar
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
