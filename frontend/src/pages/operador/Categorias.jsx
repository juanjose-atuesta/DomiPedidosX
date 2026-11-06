import { useEffect, useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import {
  actualizarCategoria,
  crearCategoria,
  listarCategorias,
  listarProductos,
} from "../../api/menu"
import { mensajeDeError } from "../../utils/errores"

const COLUMNAS = "grid grid-cols-[2fr_1fr_120px] items-center gap-4"

export default function Categorias() {
  const [categorias, setCategorias] = useState([])
  const [productos, setProductos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState("")
  const [nombre, setNombre] = useState("")
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true

    Promise.all([listarCategorias(), listarProductos(true)])
      .then(([datosCategorias, datosProductos]) => {
        if (!vigente) return
        setCategorias(datosCategorias)
        setProductos(datosProductos)
      })
      .catch((err) => {
        if (vigente) {
          setErrorCarga(mensajeDeError(err, "No se pudieron cargar las categorías."))
        }
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const limpiar = () => {
    setNombre("")
    setEditandoId(null)
    setError("")
  }

  const guardar = async (e) => {
    e.preventDefault()
    if (guardando) return
    const limpio = nombre.trim()

    if (!limpio) return setError("El nombre es obligatorio")

    const repetida = categorias.some(
      (c) => c.id !== editandoId && c.nombre.toLowerCase() === limpio.toLowerCase(),
    )
    if (repetida) return setError("Ya existe una categoría con ese nombre")

    setGuardando(true)
    try {
      if (editandoId) {
        const actualizada = await actualizarCategoria(editandoId, { nombre: limpio })
        setCategorias((cs) => cs.map((c) => (c.id === editandoId ? actualizada : c)))
      } else {
        const creada = await crearCategoria({ nombre: limpio })
        setCategorias((cs) => [...cs, creada])
      }
      limpiar()
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar la categoría."))
    } finally {
      setGuardando(false)
    }
  }

  const editar = (c) => {
    setEditandoId(c.id)
    setNombre(c.nombre)
    setError("")
  }

  const contarProductos = (categoriaId) =>
    productos.filter((p) => p.categoria_id === categoriaId).length

  return (
    <AdminLayout titulo="Categorías">
      {errorCarga && <MensajeAlerta tipo="error">{errorCarga}</MensajeAlerta>}

      <div className="flex flex-wrap items-start gap-6">
        <div className="w-full max-w-[700px] overflow-x-auto rounded-xl border border-borde bg-white p-4">
          <div className="min-w-[480px]">
            <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
              <p>Nombre</p>
              <p>Productos</p>
              <p>Acciones</p>
            </div>

            {cargando && <p className="py-4 text-sm text-texto-sec">Cargando categorías…</p>}
            {!cargando && !errorCarga && categorias.length === 0 && (
              <p className="py-4 text-sm text-texto-sec">No hay categorías registradas.</p>
            )}

            {categorias.map((c) => (
              <div key={c.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
                <p>{c.nombre}</p>
                <p>{contarProductos(c.id)}</p>
                <div>
                  <Boton tipo="secundario" onClick={() => editar(c)}>
                    Editar
                  </Boton>
                </div>
              </div>
            ))}
          </div>
        </div>

        <form
          onSubmit={guardar}
          noValidate
          className="flex w-full max-w-[320px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
            {editandoId ? "Editar categoría" : "Nueva categoría"}
          </h2>
          <CampoTexto
            etiqueta="Nombre de la categoría"
            placeholder="Escribe aquí"
            maxLength={50}
            value={nombre}
            error={error}
            onChange={(e) => {
              setNombre(e.target.value)
              setError("")
            }}
          />
          <Boton type="submit" anchoCompleto disabled={guardando}>
            {guardando ? "Guardando…" : "Guardar categoría"}
          </Boton>
          {editandoId && (
            <Boton tipo="texto" anchoCompleto onClick={limpiar}>
              Cancelar edición
            </Boton>
          )}
        </form>
      </div>
    </AdminLayout>
  )
}
