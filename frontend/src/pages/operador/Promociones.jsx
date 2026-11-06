import { useEffect, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { desactivarPromocion, listarPromocionesGestion } from "../../api/promociones"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { mensajeDeError } from "../../utils/errores"
import { fechaDeHoy, formatearFecha, moneda } from "../../utils/formato"

const COLUMNAS = "grid grid-cols-[1.4fr_0.6fr_1.2fr_0.7fr_120px_250px] items-center gap-4"
const TITULOS = ["Promoción", "Descuento", "Vigencia", "Cupo diario", "Estado", "Acciones"]
const ETIQUETA = {
  Activa: "entregado",
  Programada: "camino",
  Vencida: "cancelado",
  Inactiva: "recibido",
}

function estadoPromocion(promocion) {
  const hoy = fechaDeHoy()
  if (!promocion.activa) return "Inactiva"
  if (promocion.fecha_fin < hoy) return "Vencida"
  if (promocion.fecha_inicio > hoy) return "Programada"
  return "Activa"
}

function textoDescuento(promocion) {
  return promocion.porcentaje_descuento
    ? `${Number(promocion.porcentaje_descuento)}%`
    : moneda(promocion.monto_descuento)
}

export default function Promociones() {
  const navigate = useNavigate()
  const location = useLocation()
  const { esAdmin, sedes } = useSedesUsuario()
  const [promociones, setPromociones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState(location.state?.mensaje ?? "")
  const [aDesactivar, setADesactivar] = useState(null)
  const [procesando, setProcesando] = useState(false)

  useEffect(() => {
    let vigente = true

    listarPromocionesGestion()
      .then((datos) => {
        if (vigente) setPromociones(datos)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar las promociones."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const desactivar = async () => {
    if (!aDesactivar || procesando) return
    setProcesando(true)
    setError("")
    setMensaje("")
    try {
      await desactivarPromocion(aDesactivar.id)
      setPromociones((ps) =>
        ps.map((p) => (p.id === aDesactivar.id ? { ...p, activa: false } : p)),
      )
      setMensaje("Promoción desactivada correctamente.")
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo desactivar la promoción."))
    } finally {
      setADesactivar(null)
      setProcesando(false)
    }
  }

  const nombreSede = (sedeId) =>
    sedeId
      ? (sedes.find((s) => s.id === sedeId)?.nombre ?? "Otra sede")
      : "Todas las sedes"

  return (
    <AdminLayout
      titulo="Promociones"
      accion={<Boton onClick={() => navigate("/operador/promociones/nueva")}>Nueva promoción</Boton>}
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[960px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {cargando && <p className="py-6 text-sm text-texto-sec">Cargando promociones…</p>}
          {!cargando && promociones.length === 0 && (
            <p className="py-6 text-sm text-texto-sec">No hay promociones registradas.</p>
          )}

          {promociones.map((p) => {
            const estado = estadoPromocion(p)
            // Las promociones globales solo las gestiona el administrador.
            const editable = esAdmin || Boolean(p.sede_id)
            return (
              <div key={p.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
                <div>
                  <p>{p.nombre}</p>
                  <p className="text-xs text-texto-sec">{nombreSede(p.sede_id)}</p>
                </div>
                <p>{textoDescuento(p)}</p>
                <p>
                  {formatearFecha(p.fecha_inicio)} – {formatearFecha(p.fecha_fin)}
                </p>
                <p>{p.cupo_maximo_diario}</p>
                <div>
                  <EtiquetaEstado estado={ETIQUETA[estado]}>{estado}</EtiquetaEstado>
                </div>
                <div className="flex items-center gap-2">
                  <Boton
                    tipo="secundario"
                    disabled={!editable}
                    onClick={() => navigate(`/operador/promociones/${p.id}/editar`)}
                  >
                    Editar
                  </Boton>
                  <Boton
                    tipo="secundario"
                    disabled={!editable || !p.activa}
                    onClick={() => setADesactivar(p)}
                  >
                    Desactivar
                  </Boton>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <ModalConfirmacion
        abierto={Boolean(aDesactivar)}
        titulo="¿Desactivar promoción?"
        texto="Dejará de aplicarse a los pedidos nuevos. Los pedidos anteriores conservan el descuento."
        textoConfirmar={procesando ? "Desactivando…" : "Desactivar"}
        onConfirmar={desactivar}
        onCancelar={() => {
          if (!procesando) setADesactivar(null)
        }}
      />
    </AdminLayout>
  )
}
