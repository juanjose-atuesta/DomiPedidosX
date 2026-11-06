import { useEffect, useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import Interruptor from "../../components/Interruptor"
import MensajeAlerta from "../../components/MensajeAlerta"
import { guardarInventario, listarInventario } from "../../api/inventario"
import { listarCategorias, listarProductos } from "../../api/menu"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { mensajeDeError } from "../../utils/errores"

const COLUMNAS = "grid grid-cols-[1.3fr_1fr_90px_120px_120px_160px] items-center gap-4"
const TITULOS = ["Producto", "Categoría", "En sede", "Existencias", "Stock mínimo", "Estado"]
const STOCK_MINIMO_INICIAL = 5

function calcularEstado({ disponible, controlaStock, existencias, minimo }) {
  if (!disponible) return { estado: "recibido", texto: "No se vende aquí" }
  if (!controlaStock) return { estado: "entregado", texto: "Disponible" }
  if (existencias === 0) return { estado: "cancelado", texto: "Agotado" }
  if (existencias <= minimo) return { estado: "preparacion", texto: "Stock bajo" }
  return { estado: "entregado", texto: "Disponible" }
}

// Une todos los productos con su fila de inventario: sin fila no se venden en la sede.
function construirItems(productos, categorias, inventario) {
  return productos.map((producto) => {
    const fila = inventario.find((i) => i.producto_id === producto.id)
    return {
      id: producto.id,
      nombre: producto.nombre,
      categoria:
        categorias.find((c) => c.id === producto.categoria_id)?.nombre ?? "Sin categoría",
      disponible: fila?.disponible_en_sede ?? false,
      controlaStock: fila?.controla_stock ?? true,
      existencias: fila?.stock_actual ?? 0,
      minimo: fila?.stock_minimo ?? STOCK_MINIMO_INICIAL,
      modificado: false,
    }
  })
}

function CampoNumero({ valor, onChange, etiqueta }) {
  return (
    <input
      type="number"
      min="0"
      aria-label={etiqueta}
      value={valor}
      onChange={(e) => onChange(Math.max(0, Math.floor(Number(e.target.value) || 0)))}
      className="w-full rounded-lg border border-borde bg-white p-2.5 text-center text-sm text-texto outline-none focus:border-primario focus:ring-1 focus:ring-primario"
    />
  )
}

export default function Inventario() {
  const { sedes, cargando: cargandoSedes, error: errorSedes } = useSedesUsuario()
  const [sedeElegida, setSedeElegida] = useState("")
  const [items, setItems] = useState([])
  const [cargadoDe, setCargadoDe] = useState(null)
  const [error, setError] = useState("")
  const [guardado, setGuardado] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const sedeId = sedeElegida || sedes[0]?.id || ""

  useEffect(() => {
    if (!sedeId) return undefined
    let vigente = true

    Promise.all([listarProductos(), listarCategorias(), listarInventario(sedeId)])
      .then(([productos, categorias, inventario]) => {
        if (!vigente) return
        setItems(construirItems(productos, categorias, inventario))
        setError("")
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar el inventario."))
      })
      .finally(() => {
        if (vigente) setCargadoDe(sedeId)
      })

    return () => {
      vigente = false
    }
  }, [sedeId])

  const cambiar = (id, campo, valor) => {
    setItems((its) =>
      its.map((i) => (i.id === id ? { ...i, [campo]: valor, modificado: true } : i)),
    )
    setGuardado(false)
  }

  const guardar = async () => {
    const modificados = items.filter((i) => i.modificado)
    if (guardando || modificados.length === 0) return

    setGuardando(true)
    setError("")
    setGuardado(false)

    const resultados = await Promise.allSettled(
      modificados.map((i) =>
        guardarInventario(sedeId, {
          producto_id: i.id,
          disponible_en_sede: i.disponible,
          controla_stock: i.controlaStock,
          stock_actual: i.existencias,
          stock_minimo: i.minimo,
        }),
      ),
    )

    // Los que fallan siguen marcados como modificados para poder reintentarlos.
    const fallidos = modificados.filter((_, indice) => resultados[indice].status === "rejected")
    setItems((its) =>
      its.map((i) => ({ ...i, modificado: fallidos.some((f) => f.id === i.id) })),
    )

    if (fallidos.length > 0) {
      const primero = resultados.find((r) => r.status === "rejected")
      setError(
        `No se guardaron: ${fallidos.map((f) => f.nombre).join(", ")}. ${mensajeDeError(primero.reason)}`,
      )
    } else {
      setGuardado(true)
    }
    setGuardando(false)
  }

  const cargando = cargandoSedes || (Boolean(sedeId) && cargadoDe !== sedeId)
  const hayCambios = items.some((i) => i.modificado)
  const conEstado = items.map((i) => ({ ...i, ...calcularEstado(i) }))
  const partes = [
    ...conEstado
      .filter((i) => i.texto === "Stock bajo")
      .map((i) => `${i.nombre}: ${i.existencias} de ${i.minimo} (stock mínimo)`),
    ...conEstado.filter((i) => i.texto === "Agotado").map((i) => `${i.nombre}: sin existencias`),
  ]

  return (
    <AdminLayout
      titulo="Inventario"
      accion={
        <Boton disabled={!hayCambios || guardando} onClick={guardar}>
          {guardando ? "Guardando…" : "Guardar cambios"}
        </Boton>
      }
    >
      {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {!cargandoSedes && sedes.length === 0 && !errorSedes && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
        </MensajeAlerta>
      )}

      {sedes.length > 0 && (
        <div className="w-full max-w-[320px]">
          <CampoSelect
            etiqueta="Sede"
            opciones={sedes.map((s) => ({ valor: s.id, etiqueta: s.nombre }))}
            value={sedeId}
            onChange={(e) => {
              setSedeElegida(e.target.value)
              setGuardado(false)
            }}
          />
        </div>
      )}

      {!cargando && partes.length > 0 && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          {partes.join(". ")}.
        </MensajeAlerta>
      )}
      {guardado && <MensajeAlerta tipo="exito" className="w-fit max-w-full">Cambios guardados</MensajeAlerta>}

      {sedeId && (
        <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
          <div className="min-w-[880px]">
            <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
              {TITULOS.map((t) => (
                <p key={t}>{t}</p>
              ))}
            </div>

            {cargando ? (
              <p className="py-6 text-sm text-texto-sec">Cargando inventario…</p>
            ) : (
              conEstado.length === 0 && (
                <p className="py-6 text-sm text-texto-sec">No hay productos registrados.</p>
              )
            )}

            {!cargando &&
              conEstado.map((i) => (
                <div key={i.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
                  <p>{i.nombre}</p>
                  <p>{i.categoria}</p>
                  <div>
                    <Interruptor
                      activo={i.disponible}
                      etiqueta={`Se vende en esta sede: ${i.nombre}`}
                      onChange={(valor) => cambiar(i.id, "disponible", valor)}
                    />
                  </div>
                  <CampoNumero
                    etiqueta={`Existencias de ${i.nombre}`}
                    valor={i.existencias}
                    onChange={(v) => cambiar(i.id, "existencias", v)}
                  />
                  <CampoNumero
                    etiqueta={`Stock mínimo de ${i.nombre}`}
                    valor={i.minimo}
                    onChange={(v) => cambiar(i.id, "minimo", v)}
                  />
                  <div>
                    <EtiquetaEstado estado={i.estado}>{i.texto}</EtiquetaEstado>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
