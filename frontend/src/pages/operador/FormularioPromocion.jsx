import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import { PROMOCIONES } from "../../data/promociones"
import { PRODUCTOS } from "../../data/productos"

export default function FormularioPromocion() {
  const navigate = useNavigate()
  const { id } = useParams()
  const promo = id ? PROMOCIONES.find((p) => p.id === Number(id)) : null

  const [nombre, setNombre] = useState(promo?.nombre ?? "")
  const [descuento, setDescuento] = useState(promo?.descuento ?? "")
  const [cupo, setCupo] = useState(promo?.cupo ?? "")
  const [inicio, setInicio] = useState(promo?.inicio ?? "")
  const [fin, setFin] = useState(promo?.fin ?? "")
  const [condiciones, setCondiciones] = useState(promo?.condiciones ?? "")
  const [incluidos, setIncluidos] = useState(promo?.productos ?? [])
  const [errorProductos, setErrorProductos] = useState("")

  const volver = () => navigate("/operador/promociones")
  const porElegir = PRODUCTOS.map((p) => p.nombre).filter((n) => !incluidos.includes(n))

  const agregarProducto = (producto) => {
    if (!producto) return
    setIncluidos([...incluidos, producto])
    setErrorProductos("")
  }

  const guardar = (e) => {
    e.preventDefault()
    if (incluidos.length === 0) {
      setErrorProductos("Selecciona al menos un producto")
      return
    }
    volver()
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
      <div className="flex flex-wrap items-start gap-6">
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
              etiqueta="Tipo"
              opciones={["Descuento", "Combo"]}
              defaultValue={promo?.tipo}
            />
            <CampoTexto
              etiqueta="Descuento (%)"
              type="number"
              min="1"
              max="100"
              placeholder="Ej: 20"
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
              placeholder="Ej: pedido mínimo de $30.000"
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
                {incluidos.map((n) => (
                  <li
                    key={n}
                    className="flex items-center gap-2 rounded-full border border-borde bg-fondo px-3 py-1 text-sm text-texto"
                  >
                    {n}
                    <button
                      type="button"
                      aria-label={`Quitar ${n}`}
                      onClick={() => setIncluidos(incluidos.filter((x) => x !== n))}
                      className="text-texto-sec hover:text-primario"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <MensajeAlerta tipo="info">
            El cupo se reinicia a las 00:00 de cada día. Al agotarse, la promoción deja de estar
            disponible.
          </MensajeAlerta>

          <div className="flex items-center justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>
              Cancelar
            </Boton>
            <Boton type="submit">Guardar promoción</Boton>
          </div>
        </form>

        <aside className="flex w-full max-w-[320px] flex-col items-start gap-3 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
            Estado de la promoción
          </h2>
          <EtiquetaEstado estado={promo?.estado === "Vencida" ? "cancelado" : "entregado"}>
            {promo?.estado ?? "Activa"}
          </EtiquetaEstado>
          <p className="text-base text-texto-sec">
            Cupo de hoy: {promo?.usados ?? 0} de {cupo || "—"} usados
          </p>
        </aside>
      </div>
    </AdminLayout>
  )
}