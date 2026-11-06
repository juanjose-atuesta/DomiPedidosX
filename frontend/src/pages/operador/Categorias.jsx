import { useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"

const INICIALES = [
  { id: 1, nombre: "Hamburguesas", productos: 8 },
  { id: 2, nombre: "Acompañamientos", productos: 5 },
  { id: 3, nombre: "Bebidas", productos: 6 },
  { id: 4, nombre: "Postres", productos: 4 },
]

const COLUMNAS = "grid grid-cols-[2fr_1fr_120px] items-center gap-4"

export default function Categorias() {
  const [categorias, setCategorias] = useState(INICIALES)
  const [nombre, setNombre] = useState("")
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState("")

  const limpiar = () => {
    setNombre("")
    setEditandoId(null)
    setError("")
  }

  const guardar = (e) => {
    e.preventDefault()
    const limpio = nombre.trim()

    if (!limpio) return setError("El nombre es obligatorio")

    const repetida = categorias.some(
      (c) => c.id !== editandoId && c.nombre.toLowerCase() === limpio.toLowerCase(),
    )
    if (repetida) return setError("Ya existe una categoría con ese nombre")

    if (editandoId) {
      setCategorias((cs) => cs.map((c) => (c.id === editandoId ? { ...c, nombre: limpio } : c)))
    } else {
      setCategorias((cs) => [...cs, { id: Date.now(), nombre: limpio, productos: 0 }])
    }
    limpiar()
  }

  const editar = (c) => {
    setEditandoId(c.id)
    setNombre(c.nombre)
    setError("")
  }

  return (
    <AdminLayout titulo="Categorías">
      <div className="flex flex-wrap items-start gap-6">
        <div className="w-full max-w-[700px] overflow-x-auto rounded-xl border border-borde bg-white p-4">
          <div className="min-w-[480px]">
            <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
              <p>Nombre</p>
              <p>Productos</p>
              <p>Acciones</p>
            </div>

            {categorias.map((c) => (
              <div key={c.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
                <p>{c.nombre}</p>
                <p>{c.productos}</p>
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
          <Boton type="submit" anchoCompleto>
            Guardar categoría
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