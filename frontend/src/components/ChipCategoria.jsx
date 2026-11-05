export default function ChipCategoria({ activo = false, children, ...props }) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      className={`rounded-full border px-4 py-2 text-sm text-texto transition-colors ${
        activo
          ? "border-transparent bg-amarillo"
          : "border-borde bg-white hover:bg-fondo"
      }`}
      {...props}
    >
      {children}
    </button>
  )
}