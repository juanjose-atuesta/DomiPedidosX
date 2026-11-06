import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import ChipCategoria from "../../components/ChipCategoria"
import MensajeAlerta from "../../components/MensajeAlerta"
import TarjetaProducto from "../../components/TarjetaProducto"
import { Lupa, UbicacionPin } from "../../components/Iconos"
import BarraInferior from "../../components/BarraInferior"
import { iconoBolsaRoja } from "../../assets"
import { listarCategorias, obtenerCatalogoSede } from "../../api/menu"
import { listarSedes } from "../../api/sedes"
import { mensajeDeError } from "../../utils/errores"

const FONDO = {
  background: "linear-gradient(to top, #fff8f1 84%, #9d0208 127.76%)",
  backgroundAttachment: "fixed",
}

const CLAVE_SEDE = "domipedidos.sede"
const TODO = "todo"

function leerSedeGuardada() {
  try {
    return localStorage.getItem(CLAVE_SEDE) ?? ""
  } catch {
    return ""
  }
}

function guardarSede(id) {
  try {
    localStorage.setItem(CLAVE_SEDE, id)
  } catch {
    // Sin almacenamiento la sede solo se recuerda durante esta visita.
  }
}

export default function Inicio() {
  const navigate = useNavigate()
  const [sedes, setSedes] = useState([])
  const [categorias, setCategorias] = useState([])
  const [sedeElegida, setSedeElegida] = useState(leerSedeGuardada)
  const [productos, setProductos] = useState([])
  const [cargadoDe, setCargadoDe] = useState(null)
  const [sedesListas, setSedesListas] = useState(false)
  const [categoria, setCategoria] = useState(TODO)
  const [busqueda, setBusqueda] = useState("")
  const [error, setError] = useState("")

  const sedeId = sedes.some((s) => s.id === sedeElegida) ? sedeElegida : (sedes[0]?.id ?? "")

  useEffect(() => {
    let vigente = true

    Promise.all([listarSedes(), listarCategorias()])
      .then(([datosSedes, datosCategorias]) => {
        if (!vigente) return
        setSedes(datosSedes)
        setCategorias(datosCategorias)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar el menú."))
      })
      .finally(() => {
        if (vigente) setSedesListas(true)
      })

    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => {
    if (!sedeId) return undefined
    let vigente = true

    obtenerCatalogoSede(sedeId)
      .then((datos) => {
        if (!vigente) return
        setProductos(datos)
        setError("")
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar el menú de esta sede."))
      })
      .finally(() => {
        if (vigente) setCargadoDe(sedeId)
      })

    return () => {
      vigente = false
    }
  }, [sedeId])

  const cargando = !sedesListas || (Boolean(sedeId) && cargadoDe !== sedeId)
  const texto = busqueda.trim().toLowerCase()
  const filtrados = productos
    .filter((p) => categoria === TODO || p.categoria_id === categoria)
    .filter((p) => p.nombre.toLowerCase().includes(texto))

  const secciones = [
    { id: "combos", titulo: "Combos deli", productos: filtrados.filter((p) => p.es_combo) },
    ...categorias.map((c) => ({
      id: c.id,
      titulo: c.nombre,
      productos: filtrados.filter((p) => !p.es_combo && p.categoria_id === c.id),
    })),
    {
      id: "otros",
      titulo: "Otros",
      productos: filtrados.filter(
        (p) => !p.es_combo && !categorias.some((c) => c.id === p.categoria_id),
      ),
    },
  ].filter((s) => s.productos.length > 0)

  const verProducto = (id) => navigate(`/cliente/producto/${id}?sede=${sedeId}`)

  return (
    <div className="flex h-dvh justify-center pb-[106px]" style={FONDO}>
      <div className="h-full w-full max-w-[430px] overflow-y-auto pb-4">
        <header className="flex items-center justify-between px-[19px] pt-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium tracking-wide text-primario">DomiPedidosX</span>
            {iconoBolsaRoja && <img src={iconoBolsaRoja} alt="" className="h-[27px] w-[27px] object-cover" />}
          </div>
          <button
            type="button"
            onClick={() => navigate("/cliente/direcciones")}
            className="flex items-center gap-2 text-sm font-medium text-primario"
          >
            <UbicacionPin className="h-5 w-5" />
            Mi dirección
          </button>
        </header>

        {sedes.length > 0 && (
          <label className="mx-6 mt-4 flex h-9 items-center gap-2 rounded-full bg-fondo px-4 text-sm text-primario">
            <span className="shrink-0 font-medium">Sede:</span>
            <select
              aria-label="Sede"
              value={sedeId}
              onChange={(e) => {
                setSedeElegida(e.target.value)
                guardarSede(e.target.value)
              }}
              className="w-full bg-transparent text-sm text-texto outline-none"
            >
              {sedes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </label>
        )}

        <label className="mx-6 mt-4 flex h-9 items-center gap-2 rounded-full bg-fondo px-4">
          <Lupa className="h-5 w-5 shrink-0 text-primario" />
          <input
            type="search"
            aria-label="Buscar productos"
            placeholder="Buscar productos"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full bg-transparent text-sm text-texto outline-none placeholder:text-texto-sec"
          />
        </label>

        <div className="mt-8 flex gap-[14px] overflow-x-auto px-4 pb-1">
          <ChipCategoria activo={categoria === TODO} onClick={() => setCategoria(TODO)}>
            Todo
          </ChipCategoria>
          {categorias.map((c) => (
            <ChipCategoria key={c.id} activo={categoria === c.id} onClick={() => setCategoria(c.id)}>
              {c.nombre}
            </ChipCategoria>
          ))}
        </div>

        <main className="mt-6 flex flex-col gap-6 px-4">
          {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
          {cargando && !error && (
            <p className="py-10 text-center text-sm text-texto-sec">Cargando menú…</p>
          )}
          {!cargando && !error && secciones.length === 0 && (
            <p className="py-10 text-center text-sm text-texto-sec">No encontramos productos</p>
          )}

          {!cargando &&
            secciones.map((s) => (
              <section key={s.id} className="flex flex-col gap-2">
                <h2 className="text-base font-semibold text-black">{s.titulo}</h2>
                <div className="flex gap-[21px] overflow-x-auto pb-2">
                  {s.productos.map((p) => (
                    <div
                      key={p.id}
                      className={`w-[250px] shrink-0 ${p.agotado ? "" : "cursor-pointer"}`}
                      onClick={p.agotado ? undefined : () => verProducto(p.id)}
                    >
                      <TarjetaProducto
                        nombre={p.nombre}
                        descripcion={p.descripcion}
                        tiempo={p.tiempo_preparacion_min}
                        precio={Number(p.precio_base)}
                        imagen={p.imagen_url}
                        agotado={p.agotado}
                        onAgregar={(e) => {
                          e.stopPropagation()
                          verProducto(p.id)
                        }}
                      />
                    </div>
                  ))}
                </div>
              </section>
            ))}
        </main>
      </div>

      <BarraInferior />
    </div>
  )
}
