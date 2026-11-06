import { CANTIDAD_MAXIMA, CANTIDAD_MINIMA } from "../utils/carrito"

const BOTON =
  "flex h-8 w-8 items-center justify-center rounded-full border border-texto bg-white text-xl text-texto disabled:border-0 disabled:bg-deshabilitado disabled:text-white"

export default function SelectorCantidad({ cantidad, onCambiar, etiqueta = "" }) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        aria-label={`Quitar uno ${etiqueta}`.trim()}
        disabled={cantidad <= CANTIDAD_MINIMA}
        onClick={() => onCambiar(cantidad - 1)}
        className={BOTON}
      >
        −
      </button>
      <span aria-live="polite" className="w-6 text-center text-xl font-medium text-black">
        {cantidad}
      </span>
      <button
        type="button"
        aria-label={`Agregar uno ${etiqueta}`.trim()}
        disabled={cantidad >= CANTIDAD_MAXIMA}
        onClick={() => onCambiar(cantidad + 1)}
        className={BOTON}
      >
        +
      </button>
    </div>
  )
}
