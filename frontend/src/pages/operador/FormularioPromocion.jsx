import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"
import { listarProductos } from "../../api/menu"
import {
  actualizarPromocion,
  crearPromocion,
  obtenerPromocion,
} from "../../api/promociones"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { mensajeDeError } from "../../utils/errores"

const TIPOS = [
  { valor: "porcentaje", etiqueta: "Porcentaje" },
  { valor: "monto", etiqueta: "Monto fijo" },
]
const SEDE_GLOBAL = "global"

function Formulario({ id, promo, productos, sedes, esAdmin }) {
  const navigate = useNavigate()
  const [nombre, setNombre] = useState(promo?.nombre ?? "")
  const [sede, setSede] = useState(promo?.sede_id ?? (esAdmin ? SEDE_GLOBAL : (sedes[0]?.id ?? "")))
  const [tipo, setTipo] = useState(promo?.monto_descuento ? "monto" : "porcentaje")
  const [descuento, setDescuento] = useState(
    promo ? Number(promo.monto_descuento ?? promo.porcentaje_descuento) : "",
  )
  const [cupo, setCupo] = useState(promo?.cupo_maximo_diario ?? "")
  const [inicio, setInicio] = useState(promo?.fecha_inicio ?? "")
  const [fin, setFin] = useState(promo?.fecha_fin ?? "")
  const [pedidoMinimo, setPedidoMinimo] = useState(promo ? Number(promo.pedido_minimo) : 0)
  const [condiciones, setCondiciones] = useState(promo?.descripcion ?? "")
  const [incluidos, setIncluidos] = useState(
    promo?.productos.map((p) => ({ id: p.producto_id, nombre: p.producto_nombre })) ?? [],
  )
  const [errorProductos, setErrorProductos] = useState("")
  const [error, setError] = useState("")
  const [guardando, setGuardando] = useState(false)

  const volver = () => navigate("/operador/promociones")
  const porElegir = productos
    .filter((p) => !incluidos.some((i) => i.id === p.id))
    .map((p) => ({ valor: p.id, etiqueta: p.nombre }))
  const opcionesSede = [
    ...(esAdmin ? [{ valor: SEDE_GLOBAL, etiqueta: "Todas las sedes" }] : []),
    ...sedes.map((s) => ({ valor: s.id, etiqueta: s.nombre })),
  ]

  const agregarProducto = (productoId) => {
    const producto = productos.find((p) => p.id === productoId)
    if (!producto) return
    setIncluidos([...incluidos, { id: producto.id, nombre: producto.nombre }])
    setErrorProductos("")
  }

  const guardar = async (e) => {
    e.preventDefault()
    if (guardando) return
    if (incluidos.length === 0) {
      setErrorProductos("Selecciona al menos un producto")
      return
    }

    setGuardando(true)
    setError("")
    const datos = {
      sede_id: sede === SEDE_GLOBAL ? null : sede,
      nombre: nombre.trim(),
      descripcion: condiciones.trim(),
      porcentaje_descuento: tipo === "porcentaje" ? descuento : null,
      monto_descuento: tipo === "monto" ? descuento : null,
      pedido_minimo: pedidoMinimo === "" ? 0 : pedidoMinimo,
      cupo_maximo_diario: cupo,
      fecha_inicio: inicio,
      fecha_fin: fin,
      productos_ids: incluidos.map((i) => i.id),
    }

    try {
      if (id) {
        await actualizarPromocion(id, datos)
      } else {
        await crearPromocion(datos)
      }
      navigate("/operador/promociones", {
        state: { mensaje: "Promoción guardada correctamente." },
      })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar la promoción."))
      setGuardando(false)
    }
  }

  return (
    <AdminLayout
      titulo={id ? "Editar promoción" : "Nueva promoción"}
      accion={
        <Boton tipo="texto" onClick={volver}>
          ← Volver
        </Boton>
      }
    >
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {!esAdmin && sedes.length === 0 ? (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
        </MensajeAlerta>
      ) : (
        <form
          onSubmit={guardar}
          className="flex w-full max-w-[700px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto
              etiqueta="Nombre de la promoción"
              placeholder="Escribe aquí"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
            <CampoSelect
              etiqueta="Sede"
              opciones={opcionesSede}
              value={sede}
              onChange={(e) => setSede(e.target.value)}
            />
            <CampoSelect
              etiqueta="Tipo de descuento"
              opciones={TIPOS}
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
            />
            <CampoTexto
              etiqueta={tipo === "porcentaje" ? "Descuento (%)" : "Descuento ($)"}
              type="number"
              min="1"
              max={tipo === "porcentaje" ? "100" : undefined}
              placeholder={tipo === "porcentaje" ? "Ej: 20" : "Ej: 5000"}
              value={descuento}
              onChange={(e) => setDescuento(e.target.value)}
              required
            />
            <CampoTexto
              etiqueta="Cupo máximo diario"
              type="number"
              min="1"
              step="1"
              placeholder="Ej: 50"
              value={cupo}
              onChange={(e) => setCupo(e.target.value)}
              required
            />
            <CampoTexto
              etiqueta="Pedido mínimo ($)"
              type="number"
              min="0"
              value={pedidoMinimo}
              onChange={(e) => setPedidoMinimo(e.target.value)}
            />
            <CampoTexto
              etiqueta="Fecha de inicio"
              type="date"
              value={inicio}
              onChange={(e) => setInicio(e.target.value)}
              required
            />
            <CampoTexto
              etiqueta="Fecha de fin"
              type="date"
              min={inicio || undefined}
              value={fin}
              onChange={(e) => setFin(e.target.value)}
              required
            />
            <CampoTexto
              className="sm:col-span-2"
              etiqueta="Condiciones"
              placeholder="Ej: aplica a la segunda hamburguesa"
              value={condiciones}
              onChange={(e) => setCondiciones(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="w-full max-w-[320px]">
              <CampoSelect
                key={incluidos.length}
                etiqueta="Productos incluidos"
                opciones={porElegir}
                required={false}
                onChange={(e) => agregarProducto(e.target.value)}
              />
            </div>
            {errorProductos && (
              <p role="alert" className="text-xs text-error">
                ✕ {errorProductos}
              </p>
            )}
            {incluidos.length > 0 && (
              <ul className="flex flex-wrap gap-2">
                {incluidos.map((producto) => (
                  <li
                    key={producto.id}
                    className="flex items-center gap-2 rounded-full border border-borde bg-fondo px-3 py-1 text-sm text-texto"
                  >
                    {producto.nombre}
                    <button
                      type="button"
                      aria-label={`Quitar ${producto.nombre}`}
                      onClick={() =>
                        setIncluidos(incluidos.filter((i) => i.id !== producto.id))
                      }
                      className="text-texto-sec hover:text-primario"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar promoción"}
            </Boton>
          </div>
        </form>
      )}
    </AdminLayout>
  )
}

export default function FormularioPromocion() {
  const { id } = useParams()
  const { esAdmin, sedes, cargando: cargandoSedes, error: errorSedes } = useSedesUsuario()
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    let vigente = true

    Promise.all([listarProductos(), id ? obtenerPromocion(id) : null])
      .then(([productos, promo]) => {
        if (vigente) setDatos({ productos, promo })
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar la promoción."))
      })

    return () => {
      vigente = false
    }
  }, [id])

  if (!datos || cargandoSedes || errorSedes) {
    const problema = error || errorSedes
    return (
      <AdminLayout titulo={id ? "Editar promoción" : "Nueva promoción"}>
        <MensajeAlerta tipo={problema ? "error" : "info"}>{problema || "Cargando…"}</MensajeAlerta>
      </AdminLayout>
    )
  }

  return (
    <Formulario
      id={id}
      promo={datos.promo}
      productos={datos.productos}
      sedes={sedes}
      esAdmin={esAdmin}
    />
  )
}
