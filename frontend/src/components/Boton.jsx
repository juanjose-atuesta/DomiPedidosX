const ESTILOS = {
  primario:
    "bg-primario text-white enabled:hover:bg-vino disabled:bg-borde disabled:text-deshabilitado",
  secundario:
    "border-2 border-primario text-primario enabled:hover:bg-fondo-error disabled:border-borde disabled:text-deshabilitado",
  texto:
    "text-primario enabled:hover:bg-fondo-error disabled:text-deshabilitado",
  ambar:
    "bg-ambar text-texto enabled:hover:bg-amarillo disabled:bg-borde disabled:text-deshabilitado",
  contornoClaro:
    "border-2 border-white text-white enabled:hover:bg-white/15 disabled:border-deshabilitado disabled:text-deshabilitado",
}

export default function Boton({
  tipo = "primario",
  anchoCompleto = false,
  grande = false,
  className = "",
  children,
  ...props
}) {
  const tamano = grande ? "h-14 rounded-full" : "h-11 rounded-lg"

  return (
    <button
      type="button"
      className={`inline-flex shrink-0 items-center justify-center whitespace-nowrap px-6 text-base font-semibold transition-colors disabled:cursor-not-allowed ${tamano} ${ESTILOS[tipo]} ${anchoCompleto ? "w-full" : ""} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}