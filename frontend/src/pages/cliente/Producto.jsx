import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { FlechaIzquierda } from "../../components/Iconos"
import { fotoHamburguesa } from "../../assets"
import { PRODUCTOS } from "../../data/productos"

const moneda = (valor) => `$${valor.toLocaleString("es-CO")}`

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

export default function Producto() {
  const navigate = useNavigate()
  const { id } = useParams()
  const producto = PRODUCTOS.find((p) => p.id === Number(id))

  const [tamano, setTamano] = useState(0)
  const [adiciones, setAdiciones] = useState([])
  const [quitar, setQuitar] = useState([])
  const [observaciones, setObservaciones] = useState("")
  const [cantidad, setCantidad] = useState(1)
  const [agregado, setAgregado] = useState(false)

  if (!producto) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-fondo p-8 text-center">
        <p className="text-texto">No encontramos este producto</p>
        <button
          type="button"
          onClick={() => navigate("/cliente")}
          className="font-semibold text-primario underline"
        >
          Volver al inicio
        </button>
      </div>
    )
  }

  const alternar = (lista, setLista, indice) =>
    setLista(lista.includes(indice) ? lista.filter((i) => i !== indice) : [...lista, indice])

  const extraTamano = producto.tamanos[tamano]?.extra ?? 0
  const extraAdiciones = adiciones.reduce((suma, i) => suma + producto.adiciones[i].extra, 0)
  const total = (producto.precio + extraTamano + extraAdiciones) * cantidad
  const agotado = !producto.disponible
  const foto = producto.imagen ?? (producto.categoria === "Hamburguesas" ? fotoHamburguesa : undefined)

  return (
    <div className="flex min-h-screen justify-center bg-fondo">
      <div className="relative w-full max-w-[430px] pb-44">
        <div className="relative h-[325px] bg-borde">
          {foto ? (
            <img src={foto} alt={producto.nombre} className="h-full w-full object-cover" />
          ) : (
            <div aria-hidden="true" className="flex h-full items-center justify-center text-7xl">
              🍔
            </div>
          )}
          <button
            type="button"
            aria-label="Volver"
            onClick={() => navigate("/cliente")}
            className="absolute left-6 top-[26px] flex h-10 w-10 items-center justify-center rounded-full bg-white/80 text-texto"
          >
            <FlechaIzquierda />
          </button>
        </div>

        <div className="relative -mt-10 rounded-t-[32px] bg-fondo px-[33px] pt-9">
          <div className="flex flex-col gap-3">
            <h1 className="font-titulo text-[28px] font-semibold leading-9 text-black">
              {producto.nombre}
            </h1>
            <div className="flex items-center gap-10">
              <span className="font-titulo text-2xl font-semibold text-acento">
                {moneda(producto.precio)}
              </span>
              <span className="text-xl text-texto-sec">⏱ {producto.tiempo} min</span>
            </div>
            <p className="text-justify text-sm text-texto-sec">
              {producto.detalle ?? producto.descripcion}
            </p>
          </div>

          {producto.tamanos.length > 0 && (
            <section className="mt-8">
              <h2 className="text-xl text-black">Tamaño*</h2>
              <div className="mt-3 flex flex-col gap-3">
                {producto.tamanos.map((t, i) => (
                  <FilaOpcion
                    key={t.nombre}
                    tipo="radio"
                    grupo="tamano"
                    nombre={t.nombre}
                    extra={t.extra}
                    marcado={tamano === i}
                    onCambiar={() => setTamano(i)}
                  />
                ))}
              </div>
            </section>
          )}

          {producto.adiciones.length > 0 && (
            <section className="mt-8">
              <h2 className="text-xl text-black">
                Adiciones <span className="text-sm">(Opcional)</span>
              </h2>
              <div className="mt-3 flex flex-col gap-3">
                {producto.adiciones.map((a, i) => (
                  <FilaOpcion
                    key={a.nombre}
                    tipo="checkbox"
                    nombre={a.nombre}
                    extra={a.extra}
                    marcado={adiciones.includes(i)}
                    onCambiar={() => alternar(adiciones, setAdiciones, i)}
                  />
                ))}
              </div>
            </section>
          )}

          {producto.excluibles.length > 0 && (
            <section className="mt-8">
              <h2 className="text-xl text-black">
                Quitar ingredientes <span className="text-sm">(Opcional)</span>
              </h2>
              <div className="mt-3 flex flex-col gap-3">
                {producto.excluibles.map((x, i) => (
                  <FilaOpcion
                    key={x.nombre}
                    tipo="checkbox"
                    nombre={`Sin ${x.nombre.toLowerCase()}`}
                    extra={0}
                    marcado={quitar.includes(i)}
                    onCambiar={() => alternar(quitar, setQuitar, i)}
                  />
                ))}
              </div>
            </section>
          )}

          <section className="mt-8">
            <h2 className="text-xl text-black">
              Observaciones <span className="text-sm">(Opcional)</span>
            </h2>
            <CampoTexto
              className="mt-3"
              aria-label="Observaciones"
              placeholder="Escribe aquí"
              maxLength={200}
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
            />
          </section>
        </div>
      </div>

      <div className="fixed bottom-[22px] left-1/2 w-[calc(100%-32px)] max-w-[398px] -translate-x-1/2">
        {agregado && (
          <MensajeAlerta tipo="exito" className="mb-2">
            Agregado al carrito
          </MensajeAlerta>
        )}
        <div className="flex items-center justify-between gap-3 rounded-full bg-borde p-3 shadow-[0_4px_16px_rgba(0,0,0,0.15)]">
          <div className="flex items-center gap-3 pl-1">
            <button
              type="button"
              aria-label="Quitar uno"
              disabled={cantidad === 1}
              onClick={() => setCantidad(cantidad - 1)}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-texto bg-white text-xl text-texto disabled:border-0 disabled:bg-deshabilitado disabled:text-white"
            >
              −
            </button>
            <span aria-live="polite" className="w-6 text-center text-xl font-medium text-black">
              {cantidad}
            </span>
            <button
              type="button"
              aria-label="Agregar uno"
              onClick={() => setCantidad(Math.min(99, cantidad + 1))}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-texto bg-white text-xl text-texto"
            >
              +
            </button>
          </div>
          <button
            type="button"
            disabled={agotado || agregado}
            onClick={() => setAgregado(true)}
            className="h-11 whitespace-nowrap rounded-full bg-primario px-5 text-sm font-semibold text-white enabled:hover:bg-vino disabled:bg-deshabilitado"
          >
            {agotado ? "Agotado" : `Agregar · ${moneda(total)}`}
          </button>
        </div>
      </div>
    </div>
  )
}