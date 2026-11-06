import { useEffect, useState } from "react"
import { useNavigate, useParams, useSearchParams } from "react-router-dom"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import SelectorCantidad from "../../components/SelectorCantidad"
import SelectorOpciones from "../../components/SelectorOpciones"
import { FlechaIzquierda } from "../../components/Iconos"
import { obtenerCatalogoSede } from "../../api/menu"
import { useCarrito } from "../../context/carrito-context"
import { useSeleccionOpciones } from "../../hooks/useSeleccionOpciones"
import { CANTIDAD_MAXIMA, construirLinea } from "../../utils/carrito"
import { normalizarProducto } from "../../utils/catalogo"
import { moneda } from "../../utils/formato"

const AVISOS = {
  cargando: "Cargando producto…",
  "no-encontrado": "No encontramos este producto",
  error: "No se pudo cargar el producto. Intenta de nuevo.",
}

export default function Producto() {
  const { id } = useParams()
  const [parametros] = useSearchParams()
  const sede = parametros.get("sede")
  const [producto, setProducto] = useState(null)
  const [estado, setEstado] = useState(sede ? "cargando" : "no-encontrado")

  useEffect(() => {
    if (!sede) return undefined
    let vigente = true

    obtenerCatalogoSede(sede)
      .then((catalogo) => {
        if (!vigente) return
        const encontrado = catalogo.find((p) => p.id === id)
        setProducto(encontrado ? normalizarProducto(encontrado) : null)
        setEstado(encontrado ? "listo" : "no-encontrado")
      })
      .catch(() => {
        if (vigente) setEstado("error")
      })

    return () => {
      vigente = false
    }
  }, [id, sede])

  if (estado === "listo") return <DetalleProducto producto={producto} sede={sede} />
  return <AvisoProducto estado={estado} />
}

function AvisoProducto({ estado }) {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-fondo p-8 text-center">
      <p className="text-texto">{AVISOS[estado]}</p>
      {estado !== "cargando" && (
        <button
          type="button"
          onClick={() => navigate("/cliente")}
          className="font-semibold text-primario underline"
        >
          Volver al inicio
        </button>
      )}
    </div>
  )
}

function DetalleProducto({ producto, sede }) {
  const navigate = useNavigate()
  const { carritos, agregar } = useCarrito()
  const seleccion = useSeleccionOpciones(producto)
  const [observaciones, setObservaciones] = useState("")
  const [cantidad, setCantidad] = useState(1)
  const [aviso, setAviso] = useState("")

  const total = (producto.precio + seleccion.extra) * cantidad
  const { agotado, imagen: foto } = producto

  const agregarAlCarrito = () => {
    const linea = construirLinea(producto, seleccion.opciones, cantidad, observaciones)
    const previa = (carritos[sede] ?? []).find((l) => l.clave === linea.clave)
    agregar(sede, linea)
    setAviso(
      previa && previa.cantidad + cantidad > CANTIDAD_MAXIMA
        ? `Agregado: el máximo es ${CANTIDAD_MAXIMA} unidades de este producto`
        : "Agregado al carrito",
    )
  }

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
            <p className="text-justify text-sm text-texto-sec">{producto.descripcion}</p>
          </div>

          <div className="mt-8">
            <SelectorOpciones seleccion={seleccion} />
          </div>

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
        {aviso && (
          <MensajeAlerta tipo="exito" className="mb-2">
            {aviso}.{" "}
            <button
              type="button"
              onClick={() => navigate("/cliente/carrito")}
              className="font-semibold underline"
            >
              Ver carrito
            </button>
          </MensajeAlerta>
        )}
        <div className="flex items-center justify-between gap-3 rounded-full bg-borde p-3 shadow-[0_4px_16px_rgba(0,0,0,0.15)]">
          <div className="pl-1">
            <SelectorCantidad
              cantidad={cantidad}
              onCambiar={(nueva) => {
                setCantidad(nueva)
                setAviso("")
              }}
            />
          </div>
          <button
            type="button"
            disabled={agotado}
            onClick={agregarAlCarrito}
            className="h-11 whitespace-nowrap rounded-full bg-primario px-5 text-sm font-semibold text-white enabled:hover:bg-vino disabled:bg-deshabilitado"
          >
            {agotado ? "Agotado" : `Agregar · ${moneda(total)}`}
          </button>
        </div>
      </div>
    </div>
  )
}
