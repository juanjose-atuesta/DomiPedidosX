import { useState } from "react"
import Boton from "./Boton"
import CampoTexto from "./CampoTexto"

// Código de promoción: se aplica al pulsar "Aplicar"; el backend lo valida
// (vigencia, cupo del día, mínimo y productos) al cotizar y al confirmar.
export default function CampoPromocion({ codigoAplicado, onAplicar, error, promocion, cargando }) {
  const [codigo, setCodigo] = useState(codigoAplicado)

  if (codigoAplicado && !cargando && !error && promocion) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg bg-fondo px-4 py-3">
        <p className="min-w-0 text-sm text-texto">
          Promoción <strong>{promocion.nombre}</strong> aplicada
        </p>
        <Boton
          tipo="texto"
          pequeno
          onClick={() => {
            setCodigo("")
            onAplicar("")
          }}
        >
          Quitar
        </Boton>
      </div>
    )
  }

  return (
    <form
      className="flex items-start gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        onAplicar(codigo.trim())
      }}
    >
      <CampoTexto
        etiqueta="Código de promoción (opcional)"
        placeholder="Ej: MARTES10"
        maxLength={50}
        className="flex-1"
        value={codigo}
        error={codigoAplicado && !cargando ? error : ""}
        onChange={(e) => setCodigo(e.target.value)}
      />
      {/* Borrar el código y pulsar "Quitar" deja el pedido sin promoción. */}
      <Boton
        type="submit"
        tipo="secundario"
        className="mt-6"
        disabled={codigo.trim() === codigoAplicado || cargando}
      >
        {codigo.trim() ? "Aplicar" : "Quitar"}
      </Boton>
    </form>
  )
}
