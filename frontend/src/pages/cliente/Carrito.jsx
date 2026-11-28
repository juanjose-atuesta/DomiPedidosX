import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoPromocion from "../../components/CampoPromocion"
import CampoSelect from "../../components/CampoSelect"
import DesgloseCotizacion from "../../components/DesgloseCotizacion"
import CampoTexto from "../../components/CampoTexto"
import ListaLineasPedido from "../../components/ListaLineasPedido"
import MensajeAlerta from "../../components/MensajeAlerta"
import SelectorEntrega from "../../components/SelectorEntrega"
import { listarDirecciones } from "../../api/direcciones"
import { crearPedido } from "../../api/pedidos"
import { listarSedes } from "../../api/sedes"
import { useCarrito } from "../../context/carrito-context"
import { useCotizacion } from "../../hooks/useCotizacion"
import { etiquetaSede } from "../../utils/catalogo"
import {
  METODOS_PAGO,
  datosDeEntrega,
  detallesDePedido,
  direccionPorDefecto,
  subtotalLineas,
} from "../../utils/carrito"
import { mensajeDeError } from "../../utils/errores"

export default function Carrito() {
  const navigate = useNavigate()
  const { carritos, cambiarCantidad, quitar, vaciar, mover } = useCarrito()
  const [sedes, setSedes] = useState([])
  const [direcciones, setDirecciones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [sedeElegida, setSedeElegida] = useState("")
  const [tipo, setTipo] = useState("domicilio")
  const [direccionElegida, setDireccionElegida] = useState("")
  const [metodoPago, setMetodoPago] = useState(METODOS_PAGO[0].valor)
  const [observaciones, setObservaciones] = useState("")
  const [codigoPromocion, setCodigoPromocion] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [cambioSede, setCambioSede] = useState(null)

  useEffect(() => {
    let vigente = true

    Promise.all([listarSedes(), listarDirecciones()])
      .then(([datosSedes, datosDirecciones]) => {
        if (!vigente) return
        setSedes(datosSedes)
        setDirecciones(datosDirecciones)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar tus datos."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const sedesConLineas = Object.keys(carritos)
  const sedeId = sedesConLineas.includes(sedeElegida) ? sedeElegida : (sedesConLineas[0] ?? "")
  const lineas = carritos[sedeId] ?? []
  const subtotal = subtotalLineas(lineas)
  const nombreSede = (id) => {
    const encontrada = sedes.find((s) => s.id === id)
    return encontrada ? etiquetaSede(encontrada) : "Sede no disponible"
  }

  const direccion =
    direcciones.find((d) => d.id === direccionElegida) ?? direccionPorDefecto(direcciones)
  const faltaDireccion = tipo === "domicilio" && !direccion

  // Lo que define el precio: el backend calcula domicilio y descuento con esto.
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
  const puedeConfirmar = Boolean(cotizacion?.puede_confirmar) && !cotizando
  const sedeAlterna = cotizacion?.capacidad_llena
  ? cotizacion.sede_alterna
  : null
  const vieneDeOtraSede = cambioSede?.destinoId === sedeId

const aceptarSedeAlterna = (alterna) => {
  setCambioSede({
    origenId: sedeId,
    origenNombre: nombreSede(sedeId),
    destinoId: alterna.id,
    destinoNombre: alterna.nombre,
  })

  mover(sedeId, alterna.id)
  setSedeElegida(alterna.id)
}

const volverASedeOriginal = () => {
  mover(cambioSede.destinoId, cambioSede.origenId)
  setSedeElegida(cambioSede.origenId)
  setCambioSede(null)
}

  const confirmar = async () => {
    if (enviando || !datosPrecio || !puedeConfirmar) return

    setEnviando(true)
    setError("")

    try {
      const pedido = await crearPedido({
        ...datosPrecio,
        canal: "web",
        metodo_pago: metodoPago,
        observaciones: observaciones.trim(),
      })
      vaciar(sedeId)
      navigate("/cliente/pedido-recibido", { replace: true, state: { pedido } })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo confirmar el pedido."))
      setEnviando(false)
    }
  }

  if (sedesConLineas.length === 0) {
    return (
      <ClienteLayout titulo="Carrito" volverA="/cliente" barra>
        <p className="text-center text-sm text-texto-sec">Tu carrito está vacío</p>
        <Boton anchoCompleto onClick={() => navigate("/cliente")}>
          Ver menú
        </Boton>
      </ClienteLayout>
    )
  }

  return (
    <ClienteLayout titulo="Carrito" volverA="/cliente" barra>
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}
      {vieneDeOtraSede ? (
  <MensajeAlerta tipo="info">
    Tu pedido se hará en{" "}
    <strong>{cambioSede.destinoNombre}</strong>, porque{" "}
    {cambioSede.origenNombre} está llena.{" "}

    <button
      type="button"
      onClick={volverASedeOriginal}
      className="font-semibold underline"
    >
      Volver a mi sede
    </button>
  </MensajeAlerta>
) : (
  sedeAlterna && (
    <MensajeAlerta tipo="aviso">
      <p>
        {nombreSede(sedeId)} alcanzó su capacidad. La sede más cercana
        con cupo es <strong>{sedeAlterna.nombre}</strong>.
      </p>

      <Boton
        tipo="secundario"
        onClick={() => aceptarSedeAlterna(sedeAlterna)}
      >
        Pedir en {sedeAlterna.nombre}
      </Boton>
    </MensajeAlerta>
  )
)}
      {sedesConLineas.length > 1 ? (
        <CampoSelect
          etiqueta="Carrito de la sede"
          opciones={sedesConLineas.map((id) => ({ valor: id, etiqueta: nombreSede(id) }))}
          value={sedeId}
          onChange={(e) => setSedeElegida(e.target.value)}
        />
      ) : (
        <p className="text-sm text-texto-sec">
          Sede: <span className="font-semibold text-texto">{nombreSede(sedeId)}</span>
        </p>
      )}

      <ListaLineasPedido
        lineas={lineas}
        onCambiarCantidad={(clave, cantidad) => cambiarCantidad(sedeId, clave, cantidad)}
        onQuitar={(clave) => quitar(sedeId, clave)}
      />

      <SelectorEntrega
        tipo={tipo}
        onCambiarTipo={setTipo}
        direcciones={direcciones}
        direccionId={direccion?.id ?? ""}
        onCambiarDireccion={setDireccionElegida}
        sinDirecciones={
          !cargando && (
            <MensajeAlerta tipo="aviso">
              Aún no tienes direcciones.{" "}
              <button
                type="button"
                onClick={() =>
                  navigate("/cliente/direcciones/nueva", {
                    state: { volverA: "/cliente/carrito" },
                  })
                }
                className="font-semibold underline"
              >
                Agregar dirección
              </button>
            </MensajeAlerta>
          )
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
        placeholder="Escribe aquí"
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
        subtotalLocal={subtotal}
        tipo={tipo}
        cotizacion={cotizacion}
        cargando={cotizando}
        error={errorCotizacion}
      />

      <Boton
        grande
        anchoCompleto
        disabled={enviando || cargando || faltaDireccion || !puedeConfirmar}
        onClick={confirmar}
      >
        {enviando ? "Confirmando…" : "Confirmar pedido"}
      </Boton>
    </ClienteLayout>
  )
}
