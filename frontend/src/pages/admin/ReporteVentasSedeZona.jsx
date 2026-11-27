import { useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { obtenerVentasSedeZona } from "../../api/reportes"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

// Fecha local en formato AAAA-MM-DD (toISOString la correría un día por la zona horaria).
function aTexto(fecha) {
  const mes = String(fecha.getMonth() + 1).padStart(2, "0")
  const dia = String(fecha.getDate()).padStart(2, "0")
  return `${fecha.getFullYear()}-${mes}-${dia}`
}

function Celdas({ etiqueta, pedidos, valor, fuerte = false }) {
  const peso = fuerte ? "font-semibold text-texto" : "text-texto"
  return (
    <>
      <td className={`px-4 py-2 ${peso}`}>{etiqueta}</td>
      <td className={`px-4 py-2 text-right ${peso}`}>{pedidos}</td>
      <td className={`px-4 py-2 text-right ${peso}`}>{moneda(valor)}</td>
    </>
  )
}

// Ventas de cada sede y de cada una de sus zonas en un período (HU-10.5).
export default function ReporteVentasSedeZona() {
  const hoy = new Date()
  const [desde, setDesde] = useState(aTexto(new Date(hoy.getFullYear(), hoy.getMonth(), 1)))
  const [hasta, setHasta] = useState(aTexto(hoy))
  const [reporte, setReporte] = useState(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  const generar = async (evento) => {
    evento.preventDefault()
    if (cargando) return
    if (!desde || !hasta) {
      setError("Elige la fecha de inicio y la fecha de fin.")
      return
    }
    if (desde > hasta) {
      setError("La fecha de inicio no puede ser posterior a la fecha de fin.")
      return
    }
    setCargando(true)
    setError("")
    try {
      setReporte(await obtenerVentasSedeZona(desde, hasta))
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo generar el reporte."))
    } finally {
      setCargando(false)
    }
  }

  return (
    <AdminLayout titulo="Ventas por sede y zona">
      <form
        onSubmit={generar}
        className="flex flex-wrap items-end gap-4 rounded-xl border border-borde bg-white p-6"
      >
        <CampoTexto
          etiqueta="Fecha de inicio"
          type="date"
          value={desde}
          max={hasta || undefined}
          onChange={(e) => setDesde(e.target.value)}
          required
        />
        <CampoTexto
          etiqueta="Fecha de fin"
          type="date"
          value={hasta}
          min={desde || undefined}
          onChange={(e) => setHasta(e.target.value)}
          required
        />
        <Boton type="submit" disabled={cargando}>
          {cargando ? "Generando…" : "Generar reporte"}
        </Boton>
      </form>

      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {reporte && (
        <section className="flex flex-col gap-3">
          <p className="text-sm text-texto-sec">
            Del {reporte.desde} al {reporte.hasta}. No incluye pedidos cancelados.
          </p>
          {reporte.total_pedidos === 0 && (
            <MensajeAlerta tipo="info">No hay ventas en este período.</MensajeAlerta>
          )}
          <div className="overflow-x-auto rounded-xl border border-borde bg-white">
            <table className="w-full min-w-[480px] text-left text-sm">
              <thead className="border-b border-borde text-texto-sec">
                <tr>
                  <th className="px-4 py-2 font-medium">Sede / zona</th>
                  <th className="px-4 py-2 text-right font-medium">Pedidos</th>
                  <th className="px-4 py-2 text-right font-medium">Valor vendido</th>
                </tr>
              </thead>
              <tbody>
                {reporte.sedes.map((sede) => [
                  <tr key={sede.sede_id} className="border-t border-borde bg-fondo-error/40">
                    <Celdas
                      etiqueta={sede.sede_nombre}
                      pedidos={sede.numero_pedidos}
                      valor={sede.valor_vendido}
                      fuerte
                    />
                  </tr>,
                  ...sede.zonas.map((zona) => (
                    <tr key={`${sede.sede_id}-${zona.zona_id ?? "sin-zona"}`} className="border-t border-borde">
                      <Celdas
                        etiqueta={<span className="pl-4">{zona.zona_nombre}</span>}
                        pedidos={zona.numero_pedidos}
                        valor={zona.valor_vendido}
                      />
                    </tr>
                  )),
                ])}
              </tbody>
              <tfoot className="border-t-2 border-borde">
                <tr>
                  <Celdas
                    etiqueta="Total"
                    pedidos={reporte.total_pedidos}
                    valor={reporte.total_vendido}
                    fuerte
                  />
                </tr>
              </tfoot>
            </table>
          </div>
        </section>
      )}
    </AdminLayout>
  )
}