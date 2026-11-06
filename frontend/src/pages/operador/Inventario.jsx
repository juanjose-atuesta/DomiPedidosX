import { useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import MensajeAlerta from "../../components/MensajeAlerta"

const INICIAL = [
  { id: 1, nombre: "Hamburguesa clásica", categoria: "Hamburguesas", existencias: 24, minimo: 10 },
  { id: 2, nombre: "Papas fritas", categoria: "Acompañamientos", existencias: 8, minimo: 10 },
  { id: 3, nombre: "Limonada de coco", categoria: "Bebidas", existencias: 0, minimo: 5 },
  { id: 4, nombre: "Brownie", categoria: "Postres", existencias: 5, minimo: 5 },
]

const COLUMNAS = "grid grid-cols-[1.3fr_1fr_140px_140px_160px] items-center gap-4"
const TITULOS = ["Producto", "Categoría", "Existencias", "Stock mínimo", "Estado"]

function calcularEstado({ existencias, minimo }) {
  if (existencias === 0) return { estado: "cancelado", texto: "Agotado" }
  if (existencias <= minimo) return { estado: "preparacion", texto: "Stock bajo" }
  return { estado: "entregado", texto: "Disponible" }
}

function CampoNumero({ valor, onChange, etiqueta }) {
  return (
    <input
      type="number"
      min="0"
      aria-label={etiqueta}
      value={valor}
      onChange={(e) => onChange(Math.max(0, Math.floor(Number(e.target.value) || 0)))}
      className="w-[140px] rounded-lg border border-borde bg-white p-2.5 text-center text-sm text-texto outline-none focus:border-primario focus:ring-1 focus:ring-primario"
    />
  )
}

export default function Inventario() {
  const [items, setItems] = useState(INICIAL)
  const [guardado, setGuardado] = useState(false)

  const cambiar = (id, campo, valor) => {
    setItems((its) => its.map((i) => (i.id === id ? { ...i, [campo]: valor } : i)))
    setGuardado(false)
  }

  const conEstado = items.map((i) => ({ ...i, ...calcularEstado(i) }))
  const bajos = conEstado.filter((i) => i.texto === "Stock bajo")
  const agotados = conEstado.filter((i) => i.texto === "Agotado")
  const partes = [
    ...bajos.map((i) => `${i.nombre}: ${i.existencias} de ${i.minimo} (stock mínimo)`),
    ...agotados.map((i) => `${i.nombre}: sin existencias`),
  ]

  return (
    <AdminLayout
      titulo="Inventario"
      accion={<Boton onClick={() => setGuardado(true)}>Guardar cambios</Boton>}
    >
      {partes.length > 0 && (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          {partes.join(". ")}.
        </MensajeAlerta>
      )}
      {guardado && <MensajeAlerta tipo="exito" className="w-fit max-w-full">Cambios guardados</MensajeAlerta>}

      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[880px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {conEstado.map((i) => (
            <div key={i.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
              <p>{i.nombre}</p>
              <p>{i.categoria}</p>
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
    </AdminLayout>
  )
}