import { moneda } from "../utils/formato"

function FilaOpcion({ tipo, grupo, nombre, extra, marcado, onCambiar }) {
  const esRadio = tipo === "radio"
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded text-sm text-black has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-primario">
      <input
        type={tipo}
        name={grupo}
        checked={marcado}
        onChange={onCambiar}
        className="sr-only"
      />
      <span
        aria-hidden="true"
        className={`flex h-5 w-5 shrink-0 items-center justify-center text-xs text-white ${
          esRadio ? "rounded-full" : "rounded-md"
        } ${marcado ? "bg-primario" : "bg-texto-sec"}`}
      >
        {!esRadio && marcado && "✓"}
      </span>
      <span className="flex-1">{nombre}</span>
      {extra > 0 && <span>+{moneda(extra)}</span>}
    </label>
  )
}

function Seccion({ titulo, opcional = false, children }) {
  return (
    <section className="mt-8 first:mt-0">
      <h2 className="text-xl text-black">
        {titulo} {opcional && <span className="text-sm">(Opcional)</span>}
      </h2>
      <div className="mt-3 flex flex-col gap-3">{children}</div>
    </section>
  )
}

// `seleccion` viene de useSeleccionOpciones.
export default function SelectorOpciones({ seleccion }) {
  const { producto, tamano, adiciones, quitar } = seleccion

  return (
    <>
      {producto.tamanos.length > 0 && (
        <Seccion titulo="Tamaño*">
          {producto.tamanos.map((t, i) => (
            <FilaOpcion
              key={t.id}
              tipo="radio"
              grupo="tamano"
              nombre={t.nombre}
              extra={t.extra}
              marcado={tamano === i}
              onCambiar={() => seleccion.elegirTamano(i)}
            />
          ))}
        </Seccion>
      )}

      {producto.adiciones.length > 0 && (
        <Seccion titulo="Adiciones" opcional>
          {producto.adiciones.map((a, i) => (
            <FilaOpcion
              key={a.id}
              tipo="checkbox"
              nombre={a.nombre}
              extra={a.extra}
              marcado={adiciones.includes(i)}
              onCambiar={() => seleccion.alternarAdicion(i)}
            />
          ))}
        </Seccion>
      )}

      {producto.excluibles.length > 0 && (
        <Seccion titulo="Quitar ingredientes" opcional>
          {producto.excluibles.map((x, i) => (
            <FilaOpcion
              key={x.id}
              tipo="checkbox"
              nombre={x.nombre}
              extra={0}
              marcado={quitar.includes(i)}
              onCambiar={() => seleccion.alternarQuitar(i)}
            />
          ))}
        </Seccion>
      )}
    </>
  )
}
