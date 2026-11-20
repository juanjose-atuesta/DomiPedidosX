import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import ChipCategoria from "../../components/ChipCategoria"
import Interruptor from "../../components/Interruptor"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import {
  cambiarDisponibilidadProducto,
  desactivarProducto,
  listarCategorias,
  listarProductos,
} from "../../api/menu"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

const COLUMNAS = "grid grid-cols-[1.4fr_1.1fr_0.7fr_0.7fr_120px_250px] items-center gap-4"
const TITULOS = ["Producto", "Categoría", "Precio", "Tiempo", "Disponible", "Acciones"]
const TODAS = "todas"

export default function Productos() {
  const navigate = useNavigate()
  const location = useLocation()
  const [productos, setProductos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [categoria, setCategoria] = useState(TODAS)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState(location.state?.mensaje ?? "")
  const [aDesactivar, setADesactivar] = useState(null)
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let vigente = true

    Promise.all([listarProductos(true), listarCategorias()])
      .then(([datosProductos, datosCategorias]) => {
        if (!vigente) return
        setProductos(datosProductos)
        setCategorias(datosCategorias)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar los productos."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const visibles =
    categoria === TODAS ? productos : productos.filter((p) => p.categoria_id === categoria)

  const nombreCategoria = (id) => categorias.find((c) => c.id === id)?.nombre ?? "Sin categoría"

  const marcarDisponible = (id, disponible) =>
    setProductos((ps) => ps.map((p) => (p.id === id ? { ...p, disponible } : p)))

  const cambiarDisponible = async (id, valor) => {
    setError("")
    setMensaje("")
    try {
      await cambiarDisponibilidadProducto(id, valor)
      marcarDisponible(id, valor)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo cambiar la disponibilidad."))
    }
  }

  const desactivar = async () => {
    if (!aDesactivar || procesando) return
    setProcesando(true)
    setError("")
    setMensaje("")
    try {
      await desactivarProducto(aDesactivar.id)
      marcarDisponible(aDesactivar.id, false)
      setMensaje("Producto desactivado correctamente.")
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo desactivar el producto."))
    } finally {
      setADesactivar(null)
      setProcesando(false)
    }
  }

  return (
    <AdminLayout
      titulo="Productos"
      accion={<Boton onClick={() => navigate("/operador/productos/nuevo")}>Nuevo producto</Boton>}
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      <div className="flex flex-wrap gap-2">
        <ChipCategoria activo={categoria === TODAS} onClick={() => setCategoria(TODAS)}>
          Todas
        </ChipCategoria>
        {categorias.map((c) => (
          <ChipCategoria key={c.id} activo={categoria === c.id} onClick={() => setCategoria(c.id)}>
            {c.nombre}
          </ChipCategoria>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[900px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {cargando && <p className="py-6 text-sm text-texto-sec">Cargando productos…</p>}
          {!cargando && visibles.length === 0 && (
            <p className="py-6 text-sm text-texto-sec">No hay productos en esta categoría</p>
          )}

          {visibles.map((p) => (
            <div
              key={p.id}
              className={`${COLUMNAS} py-3 text-sm leading-5 text-texto ${p.disponible ? "" : "opacity-60"}`}
            >
              <p>{p.nombre}</p>
              <p>{nombreCategoria(p.categoria_id)}</p>
              <p>{moneda(p.precio_base)}</p>
              <p>{p.tiempo_preparacion_min} min</p>
              <div>
                <Interruptor
                  activo={p.disponible}
                  etiqueta={`Disponible: ${p.nombre}`}
                  onChange={(valor) => cambiarDisponible(p.id, valor)}
                />
              </div>
              <div className="flex items-center gap-2">
                <Boton tipo="secundario" onClick={() => navigate(`/operador/productos/${p.id}/editar`)}>
                  Editar
                </Boton>
                <Boton tipo="secundario" disabled={!p.disponible} onClick={() => setADesactivar(p)}>
                  Desactivar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ModalConfirmacion
        abierto={Boolean(aDesactivar)}
        titulo="¿Desactivar producto?"
        texto="Dejará de aparecer en el menú del cliente. Los pedidos anteriores conservan el producto."
        textoConfirmar={procesando ? "Desactivando…" : "Desactivar"}
        onConfirmar={desactivar}
        onCancelar={() => {
          if (!procesando) setADesactivar(null)
        }}
      />
    </AdminLayout>
  )
}
