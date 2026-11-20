import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"
import TarjetaProducto from "../../components/TarjetaProducto"
import {
  configurarGrupoOpciones,
  crearProducto,
  listarCategorias,
  obtenerProducto,
  reemplazarProducto,
} from "../../api/menu"
import { mensajeDeError } from "../../utils/errores"

function BloqueOpciones({ titulo, ejemplo, conPrecio = false, items, onCambiar }) {
  const [nombre, setNombre] = useState("")
  const [extra, setExtra] = useState("")

  const agregar = () => {
    const nombres = nombre.split(",").map((n) => n.trim()).filter(Boolean)
    if (nombres.length === 0) return
    const precio = conPrecio ? Math.max(0, Number(extra) || 0) : 0
    onCambiar([...items, ...nombres.map((n) => ({ nombre: n, extra: precio }))])
    setNombre("")
    setExtra("")
  }

  const quitar = (indice) => onCambiar(items.filter((_, i) => i !== indice))

  const alPulsarEnter = (e) => {
    if (e.key === "Enter") {
      e.preventDefault()
      agregar()
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-end gap-4">
        <CampoTexto
          className="w-[320px] max-w-full"
          etiqueta={titulo}
          placeholder={ejemplo}
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          onKeyDown={alPulsarEnter}
        />
        {conPrecio && (
          <CampoTexto
            className="w-[140px]"
            etiqueta="Precio extra"
            type="number"
            min="0"
            placeholder="0"
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            onKeyDown={alPulsarEnter}
          />
        )}
        <Boton tipo="texto" onClick={agregar}>
          + Agregar
        </Boton>
      </div>

      {items.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {items.map((o, i) => (
            <li
              key={`${o.nombre}-${i}`}
              className="flex items-center gap-2 rounded-full border border-borde bg-fondo px-3 py-1 text-sm text-texto"
            >
              {o.nombre}
              {o.extra > 0 && ` (+$${o.extra.toLocaleString("es-CO")})`}
              <button
                type="button"
                aria-label={`Quitar ${o.nombre}`}
                onClick={() => quitar(i)}
                className="text-texto-sec hover:text-primario"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// Grupos de opciones que maneja el formulario: el nombre se usa si el producto aún no tiene grupo.
const GRUPOS = [
  { tipo: "tamano", nombre: "Tamaños", obligatorio: true },
  { tipo: "adicion", nombre: "Adiciones", obligatorio: false },
  { tipo: "excluible", nombre: "Ingredientes excluibles", obligatorio: false },
]

function opcionesDeTipo(producto, tipo) {
  return (producto?.grupos_opcion ?? [])
    .filter((grupo) => grupo.tipo === tipo)
    .flatMap((grupo) => grupo.opciones)
    .map((opcion) => ({ nombre: opcion.nombre, extra: Number(opcion.precio_adicional) }))
}

function Formulario({ id, producto, categorias }) {
  const navigate = useNavigate()
  const [nombre, setNombre] = useState(producto?.nombre ?? "")
  const [categoriaId, setCategoriaId] = useState(producto?.categoria_id ?? "")
  const [precio, setPrecio] = useState(producto ? Number(producto.precio_base) : "")
  const [tiempo, setTiempo] = useState(producto?.tiempo_preparacion_min ?? "")
  const [descripcion, setDescripcion] = useState(producto?.descripcion ?? "")
  const [tamanos, setTamanos] = useState(opcionesDeTipo(producto, "tamano"))
  const [adiciones, setAdiciones] = useState(opcionesDeTipo(producto, "adicion"))
  const [excluibles, setExcluibles] = useState(opcionesDeTipo(producto, "excluible"))
  const [imagenUrl, setImagenUrl] = useState(producto?.imagen_url ?? "")
  const [error, setError] = useState("")
  const [guardando, setGuardando] = useState(false)
  // Si las opciones fallan tras crear el producto, reintentar lo actualiza en vez de duplicarlo.
  const idGuardado = useRef(id ?? null)

  const volver = () => navigate("/operador/productos")

  const precioInvalido = precio !== "" && !(Number(precio) > 0)

  const guardarOpciones = async (productoId) => {
    const itemsPorTipo = { tamano: tamanos, adicion: adiciones, excluible: excluibles }

    for (const { tipo, nombre: nombreGrupo, obligatorio } of GRUPOS) {
      const items = itemsPorTipo[tipo]
      const existente = producto?.grupos_opcion?.find((grupo) => grupo.tipo === tipo)
      if (items.length === 0 && !existente) continue

      await configurarGrupoOpciones(productoId, {
        nombre: existente?.nombre ?? nombreGrupo,
        tipo,
        obligatorio: obligatorio && items.length > 0,
        max_selecciones: tipo === "tamano" ? 1 : Math.max(1, items.length),
        opciones: items.map((item, orden) => ({
          nombre: item.nombre,
          precio_adicional: item.extra,
          orden,
        })),
      })
    }
  }

  const guardar = async (e) => {
    e.preventDefault()
    if (precioInvalido || guardando) return

    setGuardando(true)
    setError("")
    const datos = {
      categoria_id: categoriaId || null,
      nombre: nombre.trim(),
      descripcion: descripcion.trim(),
      precio_base: precio,
      imagen_url: imagenUrl.trim(),
      tiempo_preparacion_min: tiempo,
    }

    try {
      if (idGuardado.current) {
        await reemplazarProducto(idGuardado.current, datos)
      } else {
        const creado = await crearProducto(datos)
        idGuardado.current = creado.id
      }
      await guardarOpciones(idGuardado.current)
      navigate("/operador/productos", {
        state: { mensaje: "Producto guardado correctamente." },
      })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar el producto."))
      setGuardando(false)
    }
  }

  return (
    <AdminLayout
      titulo={id ? "Editar producto" : "Nuevo producto"}
      accion={
        <Boton tipo="texto" onClick={volver}>
          ← Volver
        </Boton>
      }
    >
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      <div className="flex flex-wrap items-start gap-6">
        <form
          onSubmit={guardar}
          className="flex w-full max-w-[704px] flex-col gap-3 rounded-xl border border-borde bg-white p-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto
              etiqueta="Nombre del producto"
              placeholder="Escribe aquí"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
            <CampoSelect
              etiqueta="Categoría"
              opciones={categorias.map((c) => ({ valor: c.id, etiqueta: c.nombre }))}
              required={false}
              value={categoriaId}
              onChange={(e) => setCategoriaId(e.target.value)}
            />
            <CampoTexto
              etiqueta="Precio"
              type="number"
              min="1"
              placeholder="Escribe aquí"
              value={precio}
              onChange={(e) => setPrecio(e.target.value)}
              error={precioInvalido ? "El precio debe ser mayor que 0" : undefined}
              required
            />
            <CampoTexto
              etiqueta="Tiempo de preparación (min)"
              type="number"
              min="1"
              placeholder="Escribe aquí"
              value={tiempo}
              onChange={(e) => setTiempo(e.target.value)}
              required
            />
            <CampoTexto
              etiqueta="URL de la imagen"
              type="url"
              placeholder="https://…"
              value={imagenUrl}
              onChange={(e) => setImagenUrl(e.target.value)}
            />
            <CampoTexto
              etiqueta="Descripción"
              placeholder="Escribe aquí"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
            />
          </div>

          <h2 className="mt-2 font-titulo text-xl font-semibold text-texto">Opciones del producto</h2>

          <BloqueOpciones
            titulo="Tamaños"
            ejemplo="Ej: Pequeño, Mediano, Grande"
            conPrecio
            items={tamanos}
            onCambiar={setTamanos}
          />
          <BloqueOpciones
            titulo="Adiciones"
            ejemplo="Ej: Queso extra, Tocineta"
            conPrecio
            items={adiciones}
            onCambiar={setAdiciones}
          />
          <BloqueOpciones
            titulo="Ingredientes excluibles"
            ejemplo="Ej: Cebolla, Tomate"
            items={excluibles}
            onCambiar={setExcluibles}
          />

          <div className="flex items-center justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar producto"}
            </Boton>
          </div>
        </form>

        <aside className="flex w-full max-w-[328px] flex-col gap-3 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">Vista previa</h2>
          <TarjetaProducto
            nombre={nombre || "Nombre del producto"}
            descripcion={descripcion || "Descripción corta"}
            tiempo={tiempo || "—"}
            precio={Number(precio) || 0}
            imagen={imagenUrl}
          />
        </aside>
      </div>
    </AdminLayout>
  )
}

export default function FormularioProducto() {
  const { id } = useParams()
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    let vigente = true

    Promise.all([listarCategorias(), id ? obtenerProducto(id) : null])
      .then(([categorias, producto]) => {
        if (vigente) setDatos({ categorias, producto })
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar el producto."))
      })

    return () => {
      vigente = false
    }
  }, [id])

  if (!datos) {
    return (
      <AdminLayout titulo={id ? "Editar producto" : "Nuevo producto"}>
        <MensajeAlerta tipo={error ? "error" : "info"}>{error || "Cargando…"}</MensajeAlerta>
      </AdminLayout>
    )
  }

  return <Formulario id={id} producto={datos.producto} categorias={datos.categorias} />
}