import Boton from "./Boton"

export default function ModalAviso({
  abierto,
  titulo,
  texto,
  textoBoton = "Regresar",
  conIcono = true,
  onCerrar,
}) {
  if (!abierto) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="aviso-titulo"
        className="flex w-full max-w-[322px] flex-col items-center gap-4 rounded-3xl bg-fondo p-6 text-center shadow-[0_8px_24px_rgba(0,0,0,0.2)]"
      >
        {conIcono && (
          <span
            aria-hidden="true"
            className="flex h-12 w-12 items-center justify-center rounded-full bg-error text-3xl font-bold text-white"
          >
            !
          </span>
        )}
        <h2 id="aviso-titulo" className="font-titulo text-xl font-semibold text-texto">
          {titulo}
        </h2>
        {texto && <p className="text-sm text-texto-sec">{texto}</p>}
        <Boton onClick={onCerrar}>{textoBoton}</Boton>
      </div>
    </div>
  )
}