import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoPromocion from "../../components/CampoPromocion"
import CampoSelect from "../../components/CampoSelect"
import DesgloseCotizacion from "../../components/DesgloseCotizacion"
import CampoTexto from "../../components/CampoTexto"
import ListaLineasPedido from "../../components/ListaLineasPedido"
import MapaDireccion from "../../components/MapaDireccion"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import SelectorCantidad from "../../components/SelectorCantidad"
import SelectorEntrega from "../../components/SelectorEntrega"
import SelectorOpciones from "../../components/SelectorOpciones"
import { obtenerCatalogoSede } from "../../api/menu"
import { crearPedido } from "../../api/pedidos"
import { buscarClientes, registrarClienteRapido } from "../../api/usuarios"
import { useCotizacion } from "../../hooks/useCotizacion"
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
import { CENTRO_MAPA } from "../../data/cobertura"
import { normalizarProducto } from "../../utils/catalogo"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

const CANALES = [
  { valor: "telefono", etiqueta: "Telefónico" },
  { valor: "mostrador", etiqueta: "Mostrador" },
]
const ESPERA_BUSQUEDA_MS = 300
// Correo interno de los clientes registrados sin correo: no se muestra.
const SIN_CORREO = "@sin-correo.invalid"
const contacto = (c) =>
  [c.telefono, c.email?.endsWith(SIN_CORREO) ? "" : c.email].filter(Boolean).join(" · ")
const TELEFONO_VALIDO = /^\d{10}$/

function RegistroRapido({ telefonoInicial, onRegistrado, onCancelar }) {
  const [nombre, setNombre] = useState("")
  const [apellido, setApellido] = useState("")
  const [telefono, setTelefono] = useState(telefonoInicial)
  const [email, setEmail] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

  const telefonoInvalido = telefono !== "" && !TELEFONO_VALIDO.test(telefono)

  const registrar = async (e) => {
    e.preventDefault()
    if (enviando || !nombre.trim() || !TELEFONO_VALIDO.test(telefono)) return
    setEnviando(true)
    setError("")
    try {
      const cliente = await registrarClienteRapido({
        nombre: nombre.trim(),
        apellido: apellido.trim(),
        telefono,
        email: email.trim(),
      })
      onRegistrado(cliente)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo registrar el cliente."))
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={registrar} className="flex flex-col gap-3 rounded-lg bg-fondo p-3">
      <p className="text-sm font-semibold text-texto">Registro rápido de cliente</p>
      <CampoTexto
        etiqueta="Nombre*"
        maxLength={100}
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
        required
      />
      <CampoTexto
        etiqueta="Apellido"
        maxLength={100}
        value={apellido}
        onChange={(e) => setApellido(e.target.value)}
      />
      <CampoTexto
        etiqueta="Teléfono* (10 dígitos)"
        type="tel"
        inputMode="numeric"
        maxLength={10}
        value={telefono}
        error={telefonoInvalido ? "Debe tener exactamente 10 dígitos" : ""}
        onChange={(e) => setTelefono(e.target.value.replace(/\D/g, ""))}
        required
      />
      <CampoTexto
        etiqueta="Correo (opcional)"
        type="email"
        maxLength={150}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      <div className="flex justify-end gap-2">
        <Boton tipo="texto" onClick={onCancelar}>
          Cancelar
        </Boton>
        <Boton
          type="submit"
          disabled={enviando || !nombre.trim() || !TELEFONO_VALIDO.test(telefono)}
        >
          {enviando ? "Registrando…" : "Registrar y usar"}
        </Boton>
      </div>
    </form>
  )
}
const TARJETA = "flex flex-col gap-4 rounded-xl border border-borde bg-white p-6"
const TITULO = "font-titulo text-xl font-semibold text-texto"

function SelectorCliente({ cliente, onElegir }) {
  const [busqueda, setBusqueda] = useState("")
  const [resultados, setResultados] = useState([])
  const [buscadoDe, setBuscadoDe] = useState(null)
  const [error, setError] = useState("")
  const [registrando, setRegistrando] = useState(false)

  useEffect(() => {
    if (cliente || registrando) return undefined
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
  }, [busqueda, cliente, registrando])

  if (cliente) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg bg-fondo p-3">
        <div className="min-w-0">
          <p className="font-semibold text-texto">
            {cliente.nombre} {cliente.apellido}
          </p>
          <p className="text-xs text-texto-sec">{contacto(cliente)}</p>
        </div>
        <Boton tipo="texto" onClick={() => onElegir(null)}>
          Cambiar
        </Boton>
      </div>
    )
  }

  if (registrando) {
    const soloDigitos = busqueda.replace(/\D/g, "")
    return (
      <RegistroRapido
        telefonoInicial={soloDigitos.length === 10 ? soloDigitos : ""}
        onCancelar={() => setRegistrando(false)}
        onRegistrado={(nuevo) => {
          setRegistrando(false)
          onElegir(nuevo)
        }}
      />
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
        <p className="text-sm text-texto-sec">
          No encontramos clientes. A un cliente nuevo búscalo con su correo o teléfono exactos.
        </p>
      )}
      <Boton tipo="texto" pequeno className="self-start" onClick={() => setRegistrando(true)}>
        + Registrar cliente nuevo
      </Boton>
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
              <span className="block text-xs text-texto-sec">{contacto(c)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

// Dirección tomada por teléfono: se marca en el mapa solo para este pedido.
function DireccionManual({ texto, posicion, onCambiarTexto, onCambiarPosicion, onVolver }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg bg-fondo p-3">
      <CampoTexto
        etiqueta="Dirección de entrega"
        placeholder="Calle 5 # 38 - 20, apto 301"
        value={texto}
        onChange={(e) => onCambiarTexto(e.target.value)}
      />
      <p className="text-xs text-texto-sec">
        {posicion
          ? `Punto marcado: ${posicion[0].toFixed(5)}, ${posicion[1].toFixed(5)}`
          : "Toca el mapa para marcar el punto de entrega"}
      </p>
      <MapaDireccion posicion={posicion ?? CENTRO_MAPA} onSeleccionar={onCambiarPosicion} />
      {onVolver && (
        <Boton tipo="texto" pequeno className="self-start" onClick={onVolver}>
          Usar una dirección guardada
        </Boton>
      )}
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
  const [usarManual, setUsarManual] = useState(false)
  const [manualTexto, setManualTexto] = useState("")
  const [manualPosicion, setManualPosicion] = useState(null)
  const [metodoPago, setMetodoPago] = useState(METODOS_PAGO[0].valor)
  const [observaciones, setObservaciones] = useState("")
  const [codigoPromocion, setCodigoPromocion] = useState("")
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
  const manual = usarManual || (cliente && direcciones.length === 0)
  const direccionManual =
    manualTexto.trim() && manualPosicion
      ? {
          direccion_texto: manualTexto.trim(),
          detalles: "",
          latitud: manualPosicion[0].toFixed(6),
          longitud: manualPosicion[1].toFixed(6),
        }
      : null
  const direccion = manual
    ? direccionManual
    : (direcciones.find((d) => d.id === direccionElegida) ?? direccionPorDefecto(direcciones))
  const faltaDireccion = tipo === "domicilio" && !direccion

  const datosPrecio =
    lineas.length > 0 && !faltaDireccion
      ? {
          sede_id: sedeId,
          tipo,
          detalles: detallesDePedido(lineas),
          codigo_promocion: codigoPromocion,
          ...(tipo === "domicilio" ? datosDeEntrega(direccion) : {}),
        }
      : null
  const { cotizacion, cargando: cotizando, error: errorCotizacion } = useCotizacion(datosPrecio)
  const listo =
    Boolean(cliente) &&
    Boolean(datosPrecio) &&
    Boolean(cotizacion?.puede_confirmar) &&
    !cotizando &&
    !enviando

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
        ...datosPrecio,
        cliente_id: cliente.id,
        canal,
        metodo_pago: metodoPago,
        observaciones: observaciones.trim(),
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
                setUsarManual(false)
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
              direcciones={manual ? [] : direcciones}
              direccionId={direccion?.id ?? ""}
              onCambiarDireccion={setDireccionElegida}
              sinDirecciones={
                cliente ? (
                  <DireccionManual
                    texto={manualTexto}
                    posicion={manualPosicion}
                    onCambiarTexto={setManualTexto}
                    onCambiarPosicion={setManualPosicion}
                    onVolver={direcciones.length > 0 ? () => setUsarManual(false) : null}
                  />
                ) : (
                  <MensajeAlerta tipo="aviso">Elige un cliente para ver sus direcciones.</MensajeAlerta>
                )
              }
            />
            {tipo === "domicilio" && cliente && !manual && (
              <Boton tipo="texto" pequeno className="self-start" onClick={() => setUsarManual(true)}>
                Usar otra dirección
              </Boton>
            )}
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

            <CampoPromocion
              codigoAplicado={codigoPromocion}
              onAplicar={setCodigoPromocion}
              error={cotizacion?.error_promocion}
              promocion={cotizacion?.promocion}
              cargando={cotizando}
            />
            <DesgloseCotizacion
              subtotalLocal={subtotalLineas(lineas)}
              tipo={tipo}
              cotizacion={cotizacion}
              cargando={cotizando}
              error={errorCotizacion}
            />
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
