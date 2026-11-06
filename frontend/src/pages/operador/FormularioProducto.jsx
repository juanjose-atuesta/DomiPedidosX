import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import TarjetaProducto from "../../components/TarjetaProducto"
import { CATEGORIAS, PRODUCTOS } from "../../data/productos"

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

export default function FormularioProducto() {
  const navigate = useNavigate()
  const { id } = useParams()
  const producto = id ? PRODUCTOS.find((p) => p.id === Number(id)) : null

  const [nombre, setNombre] = useState(producto?.nombre ?? "")
  const [precio, setPrecio] = useState(producto?.precio ?? "")
  const [tiempo, setTiempo] = useState(producto?.tiempo ?? "")
  const [descripcion, setDescripcion] = useState(producto?.descripcion ?? "")
  const [tamanos, setTamanos] = useState(producto?.tamanos ?? [])
  const [adiciones, setAdiciones] = useState(producto?.adiciones ?? [])
  const [excluibles, setExcluibles] = useState(producto?.excluibles ?? [])
  const [imagenUrl, setImagenUrl] = useState(null)
  const [imagenNombre, setImagenNombre] = useState("")

  const volver = () => navigate("/operador/productos")

  useEffect(() => {
    return () => {
      if (imagenUrl) URL.revokeObjectURL(imagenUrl)
    }
  }, [imagenUrl])

  const elegirImagen = (archivo) => {
    if (!archivo || !archivo.type.startsWith("image/")) return
    setImagenUrl(URL.createObjectURL(archivo))
    setImagenNombre(archivo.name)
  }

  const guardar = (e) => {
    e.preventDefault()
    volver()
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
              opciones={CATEGORIAS}
              defaultValue={producto?.categoria}
            />
            <CampoTexto
              etiqueta="Precio"
              type="number"
              min="1"
              placeholder="Escribe aquí"
              value={precio}
              onChange={(e) => setPrecio(e.target.value)}
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

            <div className="flex flex-col gap-[6px]">
              <span className="text-sm text-texto">Subir imagen</span>
              <label
                htmlFor="imagen-producto"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  elegirImagen(e.dataTransfer.files[0])
                }}
                className="flex h-24 w-full cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-deshabilitado bg-borde px-4 text-center text-sm text-texto-sec hover:bg-borde/70"
              >
                {imagenNombre || "Arrastra o selecciona una imagen"}
              </label>
              <input
                id="imagen-producto"
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={(e) => elegirImagen(e.target.files[0])}
              />
            </div>
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
            <Boton type="submit">Guardar producto</Boton>
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