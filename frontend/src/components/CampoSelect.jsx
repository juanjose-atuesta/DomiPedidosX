import { useId } from "react"

export default function CampoSelect({
  etiqueta,
  opciones = [],
  placeholder = "Seleccionar",
  className = "",
  required = true,
  value,
  ...props
}) {
  const id = useId()
  const controlado = value !== undefined

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {etiqueta && (
        <label htmlFor={id} className="text-sm text-texto">
          {etiqueta}
        </label>
      )}
      <select
        id={id}
        {...(controlado ? { value } : { defaultValue: "" })}
        required={required}
        className="h-11 w-full rounded-lg border border-borde bg-white px-4 text-base text-texto outline-none focus:border-primario focus:ring-1 focus:ring-primario invalid:text-deshabilitado"
        {...props}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {opciones.map((opcion, indice) => {
          const esObjeto = opcion && typeof opcion === "object"
          const valor = esObjeto ? (opcion.valor ?? opcion.value) : opcion
          const texto = esObjeto
            ? (opcion.etiqueta ?? opcion.label ?? valor)
            : opcion

          return (
            <option key={`${valor}-${indice}`} value={valor}>
              {texto}
            </option>
          )
        })}
      </select>
    </div>
  )
}