import Boton from "./Boton"

export default function ModalConfirmacion({
  abierto,
  titulo,
  texto,
  textoConfirmar = "Confirmar",
  textoCancelar = "Cancelar",
  onConfirmar,
  onCancelar,
  children,
}) {
  if (!abierto) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-titulo"
        className="flex w-full max-w-[400px] flex-col gap-4 rounded-2xl bg-white p-6 shadow-[0_8px_24px_rgba(0,0,0,0.2)]"
      >
        <h2 id="modal-titulo" className="font-titulo text-xl font-semibold text-texto">
          {titulo}
        </h2>
        {texto && <p className="text-sm text-texto-sec">{texto}</p>}
        {children}
        <div className="flex justify-end gap-3">
          <Boton tipo="secundario" onClick={onCancelar}>{textoCancelar}</Boton>
          <Boton onClick={onConfirmar}>{textoConfirmar}</Boton>
        </div>
      </div>
    </div>
  )
}