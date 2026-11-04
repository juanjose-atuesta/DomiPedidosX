import { useId } from "react"

export default function CampoSelect({
  etiqueta,
  opciones = [],
  placeholder = "Seleccionar",
  className = "",
  required = true,
  ...props
}) {
  const id = useId()
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {etiqueta && (
        <label htmlFor={id} className="text-sm text-texto">
          {etiqueta}
        </label>
      )}
      <select
        id={id}
        defaultValue=""
        required={required}
        className="h-11 w-full rounded-lg border border-borde bg-white px-4 text-base text-texto outline-none focus:border-primario focus:ring-1 focus:ring-primario invalid:text-deshabilitado"
        {...props}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {opciones.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  )
}