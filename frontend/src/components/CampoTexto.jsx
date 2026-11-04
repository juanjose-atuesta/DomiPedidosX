import { useId } from "react"

const BORDE = {
  claro: {
    normal: "border-borde focus:border-primario focus:ring-1 focus:ring-primario",
    error: "border-error ring-1 ring-error",
  },
  oscuro: {
    normal: "border-borde focus:border-amarillo focus:ring-1 focus:ring-amarillo",
    error: "border-amarillo ring-1 ring-amarillo",
  },
}

export default function CampoTexto({
  etiqueta,
  error,
  fondo = "claro",
  className = "",
  ...props
}) {
  const id = useId()
  const oscuro = fondo === "oscuro"

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {etiqueta && (
        <label htmlFor={id} className={`text-sm ${oscuro ? "text-white" : "text-texto"}`}>
          {etiqueta}
        </label>
      )}
      <input
        id={id}
        aria-invalid={Boolean(error)}
        className={`h-11 w-full rounded-lg border bg-white px-4 text-base text-texto outline-none placeholder:text-deshabilitado disabled:bg-fondo disabled:text-deshabilitado ${
          error ? BORDE[fondo].error : BORDE[fondo].normal
        }`}
        {...props}
      />
      {error && (
        <p
          role="alert"
          className={`text-xs text-error ${oscuro ? "rounded bg-fondo-error px-2 py-1" : ""}`}
        >
          ✕ {error}
        </p>
      )}
    </div>
  )
}