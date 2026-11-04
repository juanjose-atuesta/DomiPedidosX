export default function Interruptor({ activo = false, onChange, disabled = false, etiqueta }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={activo}
      aria-label={etiqueta}
      disabled={disabled}
      onClick={() => onChange?.(!activo)}
      className={`flex h-6 w-11 items-center rounded-full p-[3px] transition-colors disabled:opacity-50 ${
        activo ? "bg-exito" : "bg-deshabilitado"
      }`}
    >
      <span
        className={`h-[18px] w-[18px] rounded-full bg-white transition-transform ${
          activo ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  )
}