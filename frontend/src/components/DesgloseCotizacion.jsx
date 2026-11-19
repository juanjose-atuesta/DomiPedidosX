import MensajeAlerta from "./MensajeAlerta"
import { moneda } from "../utils/formato"

function Fila({ etiqueta, valor, destacado = false, className = "" }) {
  return (
    <div className={`flex items-center justify-between gap-3 ${className}`}>
      <span className={destacado ? "text-base font-semibold text-texto" : "text-sm text-texto-sec"}>
        {etiqueta}
      </span>
      <span
        className={
          destacado
            ? "font-titulo text-2xl font-semibold text-acento"
            : "text-sm font-semibold text-texto"
        }
      >
        {valor}
      </span>
    </div>
  )
}

// Subtotal, descuento de la promoción, domicilio según la zona y total,
// tal como los calcula el backend. Mientras llega la respuesta muestra el
// subtotal local para que el resumen no salte.
export default function DesgloseCotizacion({ subtotalLocal, tipo, cotizacion, cargando, error }) {
  const subtotal = cotizacion?.subtotal ?? subtotalLocal
  const descuento = Number(cotizacion?.descuento ?? 0)
  const esDomicilio = tipo === "domicilio"
  const pendiente = cargando ? "Calculando…" : "—"

  return (
    <div className="flex flex-col gap-2 border-t border-borde pt-4">
      <Fila etiqueta="Subtotal" valor={moneda(subtotal)} />
      {descuento > 0 && (
        <Fila
          etiqueta={`Descuento${cotizacion.promocion ? ` (${cotizacion.promocion.nombre})` : ""}`}
          valor={`−${moneda(descuento)}`}
          className="[&>span:last-child]:text-exito"
        />
      )}
      {esDomicilio && (
        <Fila
          etiqueta={
            cotizacion?.zona ? `Domicilio (${cotizacion.zona.nombre})` : "Domicilio"
          }
          valor={cotizacion ? moneda(cotizacion.costo_domicilio) : pendiente}
        />
      )}
      <Fila
        etiqueta="Total"
        valor={cotizacion ? moneda(cotizacion.total) : pendiente}
        destacado
        className="pt-1"
      />
      {cotizacion?.tiempo_estimado_min > 0 && cotizacion.puede_confirmar && (
        <p className="text-xs text-texto-sec">
          Tiempo estimado: {cotizacion.tiempo_estimado_min} min
        </p>
      )}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {cotizacion?.problemas
        ?.filter((p) => p !== cotizacion.error_promocion)
        .map((problema) => (
          <MensajeAlerta key={problema} tipo="aviso">
            {problema}
          </MensajeAlerta>
        ))}
    </div>
  )
}
