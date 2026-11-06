import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import ListaLineasPedido from "../../components/ListaLineasPedido"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import SelectorCantidad from "../../components/SelectorCantidad"
import SelectorEntrega from "../../components/SelectorEntrega"
import SelectorOpciones from "../../components/SelectorOpciones"
import { obtenerCatalogoSede } from "../../api/menu"
import { crearPedido } from "../../api/pedidos"
import { buscarClientes } from "../../api/usuarios"
import { useSedesUsuario } from "../../hooks/useSedesUsuario"
import { useSeleccionOpciones } from "../../hooks/useSeleccionOpciones"
import {
  METODOS_PAGO,
  agregarLinea,
  cambiarCantidadLinea,
  construirLinea,
  datosDeEntrega,
  detallesDePedido,
  direccionPorDefecto,
  quitarLinea,
  subtotalLineas,
} from "../../utils/carrito"
import { normalizarProducto } from "../../utils/catalogo"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

const CANALES = [
  { valor: "telefono", etiqueta: "Telefónico" },
  { valor: "mostrador", etiqueta: "Mostrador" },
]
const ESPERA_BUSQUEDA_MS = 300
const TARJETA = "flex flex-col gap-4 rounded-xl border border-borde bg-white p-6"
const TITULO = "font-titulo text-xl font-semibold text-texto"

function SelectorCliente({ cliente, onElegir }) {
  const [busqueda, setBusqueda] = useState("")
  const [resultados, setResultados] = useState([])
  const [buscadoDe, setBuscadoDe] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    if (cliente) return undefined
    let vigente = true

    const temporizador = setTimeout(() => {
      buscarClientes(busqueda)
        .then((datos) => {
          if (!vigente) return
          setResultados(datos)
          setError("")
        })
        .catch((err) => {
          if (vigente) setError(mensajeDeError(err, "No se pudieron buscar clientes."))
        })
        .finally(() => {
          if (vigente) setBuscadoDe(busqueda)
        })
    }, ESPERA_BUSQUEDA_MS)

    return () => {
      vigente = false
      clearTimeout(temporizador)
    }
  }, [busqueda, cliente])

  if (cliente) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg bg-fondo p-3">
        <div className="min-w-0">
          <p className="font-semibold text-texto">
            {cliente.nombre} {cliente.apellido}
          </p>
          <p className="text-xs text-texto-sec">
            {cliente.telefono} · {cliente.email}
          </p>
        </div>
        <Boton tipo="texto" onClick={() => onElegir(null)}>
          Cambiar
        </Boton>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <CampoTexto
        etiqueta="Buscar cliente"
        placeholder="Nombre, correo o teléfono"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {buscadoDe === busqueda && !error && resultados.length === 0 && (
        <p className="text-sm text-texto-sec">No encontramos clientes activos.</p>
      )}
      <ul className="flex max-h-56 flex-col gap-1 overflow-y-auto">
        {resultados.map((c) => (
          <li key={c.id}>
            <button
              type="button"
              onClick={() => onElegir(c)}
              className="w-full rounded-lg px-3 py-2 text-left text-sm text-texto hover:bg-fondo"
            >
              <span className="font-semibold">
                {c.nombre} {c.apellido}
              </span>
              <span className="block text-xs text-texto-sec">
                {c.telefono} · {c.email}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ModalProducto({ producto, onAgregar, onCerrar }) {
  const seleccion = useSeleccionOpciones(producto)
  const [cantidad, setCantidad] = useState(1)
  const [notas, setNotas] = useState("")

  return (
    <ModalConfirmacion
      abierto
      titulo={producto.nombre}
      textoConfirmar={`Agregar · ${moneda((producto.precio + seleccion.extra) * cantidad)}`}
      onConfirmar={() => onAgregar(construirLinea(producto, seleccion.opciones, cantidad, notas))}
      onCancelar={onCerrar}
    >
      <div className="flex max-h-[50vh] flex-col gap-4 overflow-y-auto">
        <div>
          <SelectorOpciones seleccion={seleccion} />
        </div>
        <CampoTexto
          etiqueta="Notas del producto (opcional)"
          maxLength={200}
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
        />
        <SelectorCantidad cantidad={cantidad} onCambiar={setCantidad} />
      </div>
    </ModalConfirmacion>
  )
}

export default function NuevoPedido() {
  const navigate = useNavigate()
  const { sedes, cargando: cargandoSedes, error: errorSedes } = useSedesUsuario()
  const [sedeElegida, setSedeElegida] = useState("")
  const [cliente, setCliente] = useState(null)
  const [catalogo, setCatalogo] = useState([])
  const [cargadoDe, setCargadoDe] = useState(null)
  const [filtro, setFiltro] = useState("")
  const [enModal, setEnModal] = useState(null)
  const [lineas, setLineas] = useState([])
  const [canal, setCanal] = useState(CANALES[0].valor)
  const [tipo, setTipo] = useState("recoger")
  const [direccionElegida, setDireccionElegida] = useState("")
  const [metodoPago, setMetodoPago] = useState(METODOS_PAGO[0].valor)
  const [observaciones, setObservaciones] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  const sedeId = sedeElegida || sedes[0]?.id || ""

  useEffect(() => {
    if (!sedeId) return undefined
    let vigente = true

    obtenerCatalogoSede(sedeId)
      .then((datos) => {
        if (!vigente) return
        setCatalogo(datos.map(normalizarProducto))
        setError("")
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudo cargar el menú de la sede."))
      })
      .finally(() => {
        if (vigente) setCargadoDe(sedeId)
      })

    return () => {
      vigente = false
    }
  }, [sedeId])

  const direcciones = cliente?.direcciones ?? []
  const direccion =
    direcciones.find((d) => d.id === direccionElegida) ?? direccionPorDefecto(direcciones)
  const faltaDireccion = tipo === "domicilio" && !direccion
  const listo = Boolean(cliente) && lineas.length > 0 && !faltaDireccion && !enviando

  const texto = filtro.trim().toLowerCase()
  const visibles = catalogo.filter((p) => p.nombre.toLowerCase().includes(texto))

  const cambiarSede = (id) => {
    // Cada sede tiene su propio menú e inventario.
    setSedeElegida(id)
    setLineas([])
  }

  const confirmar = async () => {
    if (!listo) return

    setEnviando(true)
    setError("")

    try {
      const pedido = await crearPedido({
        sede_id: sedeId,
        cliente_id: cliente.id,
        canal,
        tipo,
        metodo_pago: metodoPago,
        observaciones: observaciones.trim(),
        detalles: detallesDePedido(lineas),
        ...(tipo === "domicilio" ? datosDeEntrega(direccion) : {}),
      })
      navigate("/operador/pedidos", {
        state: { mensaje: `Pedido #${pedido.id} registrado correctamente.` },
      })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo registrar el pedido."))
      setEnviando(false)
    }
  }

  return (
    <AdminLayout
      titulo="Nuevo pedido"
      accion={
        <Boton tipo="texto" onClick={() => navigate("/operador/pedidos")}>
          ← Volver
        </Boton>
      }
    >
      {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {!cargandoSedes && !errorSedes && sedes.length === 0 ? (
        <MensajeAlerta tipo="aviso" className="w-fit max-w-full">
          No tienes sedes asignadas. Pide a un administrador que te asigne una.
        </MensajeAlerta>
      ) : (
        <div className="grid items-start gap-6 xl:grid-cols-[1fr_1fr_1fr]">
          <section aria-label="Cliente y sede" className={TARJETA}>
            <h2 className={TITULO}>Cliente y sede</h2>
            <SelectorCliente
              cliente={cliente}
              onElegir={(elegido) => {
                setCliente(elegido)
                setDireccionElegida("")
              }}
            />
            <CampoSelect
              etiqueta="Sede"
              opciones={sedes.map((s) => ({ valor: s.id, etiqueta: s.nombre }))}
              value={sedeId}
              onChange={(e) => cambiarSede(e.target.value)}
            />
            <CampoSelect
              etiqueta="Canal"
              opciones={CANALES}
              value={canal}
              onChange={(e) => setCanal(e.target.value)}
            />
          </section>

          <section aria-label="Menú" className={TARJETA}>
            <h2 className={TITULO}>Menú de la sede</h2>
            <CampoTexto
              etiqueta="Buscar producto"
              placeholder="Escribe aquí"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
            />
            {cargadoDe !== sedeId ? (
              <p className="text-sm text-texto-sec">Cargando menú…</p>
            ) : (
              visibles.length === 0 && (
                <p className="text-sm text-texto-sec">No hay productos para mostrar.</p>
              )
            )}
            <ul className="flex flex-col gap-2">
              {visibles.map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-texto">{p.nombre}</p>
                    <p className="text-xs text-texto-sec">{moneda(p.precio)}</p>
                  </div>
                  <Boton
                    tipo="secundario"
                    disabled={p.agotado}
                    aria-label={`Agregar ${p.nombre}`}
                    onClick={() => setEnModal(p)}
                  >
                    {p.agotado ? "Agotado" : "Agregar"}
                  </Boton>
                </li>
              ))}
            </ul>
          </section>

          <section aria-label="Resumen" className={TARJETA}>
            <h2 className={TITULO}>Resumen</h2>
            {lineas.length === 0 ? (
              <p className="text-sm text-texto-sec">Aún no has agregado productos.</p>
            ) : (
              <ListaLineasPedido
                lineas={lineas}
                onCambiarCantidad={(clave, cantidad) =>
                  setLineas((ls) => cambiarCantidadLinea(ls, clave, cantidad))
                }
                onQuitar={(clave) => setLineas((ls) => quitarLinea(ls, clave))}
              />
            )}

            <SelectorEntrega
              tipo={tipo}
              onCambiarTipo={setTipo}
              direcciones={direcciones}
              direccionId={direccion?.id ?? ""}
              onCambiarDireccion={setDireccionElegida}
              sinDirecciones={
                <MensajeAlerta tipo="aviso">
                  {cliente
                    ? "Este cliente no tiene direcciones guardadas."
                    : "Elige un cliente para ver sus direcciones."}
                </MensajeAlerta>
              }
            />
            <CampoSelect
              etiqueta="Método de pago"
              opciones={METODOS_PAGO}
              value={metodoPago}
              onChange={(e) => setMetodoPago(e.target.value)}
            />
            <CampoTexto
              etiqueta="Notas del pedido (opcional)"
              maxLength={200}
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
            />

            <div className="flex items-center justify-between border-t border-borde pt-4">
              <span className="font-semibold text-texto">Subtotal</span>
              <span className="font-titulo text-2xl font-semibold text-acento">
                {moneda(subtotalLineas(lineas))}
              </span>
            </div>
            <Boton anchoCompleto disabled={!listo} onClick={confirmar}>
              {enviando ? "Registrando…" : "Registrar pedido"}
            </Boton>
          </section>
        </div>
      )}

      {enModal && (
        <ModalProducto
          key={enModal.id}
          producto={enModal}
          onCerrar={() => setEnModal(null)}
          onAgregar={(linea) => {
            setLineas((ls) => agregarLinea(ls, linea))
            setEnModal(null)
          }}
        />
      )}
    </AdminLayout>
  )
}
