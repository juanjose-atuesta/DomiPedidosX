const TIPOS = {
  exito: { simbolo: "✓", caja: "bg-fondo-exito border-exito", icono: "bg-exito text-white" },
  error: { simbolo: "✕", caja: "bg-fondo-error border-error", icono: "bg-error text-white" },
  aviso: { simbolo: "!", caja: "bg-fondo-aviso border-ambar", icono: "bg-ambar text-texto" },
  info: { simbolo: "i", caja: "bg-fondo-info border-info", icono: "bg-info text-white" },
}

export default function MensajeAlerta({ tipo = "info", className = "", children }) {
  const { simbolo, caja, icono } = TIPOS[tipo]
  return (
    <div
      role={tipo === "error" ? "alert" : "status"}
      className={`flex items-center gap-3 rounded-lg border px-4 py-3 text-sm text-texto ${caja} ${className}`}
    >
      <span
        aria-hidden="true"
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${icono}`}
      >
        {simbolo}
      </span>
      <span>{children}</span>
    </div>
  )
}