import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import ListaLineasPedido from "../../components/ListaLineasPedido"
import MensajeAlerta from "../../components/MensajeAlerta"
import SelectorEntrega from "../../components/SelectorEntrega"
import { listarDirecciones } from "../../api/direcciones"
import { crearPedido } from "../../api/pedidos"
import { listarSedes } from "../../api/sedes"
import { useCarrito } from "../../context/carrito-context"
import { etiquetaSede } from "../../utils/catalogo"
import {
  METODOS_PAGO,
  datosDeEntrega,
  detallesDePedido,
  direccionPorDefecto,
  subtotalLineas,
} from "../../utils/carrito"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

export default function Carrito() {
  const navigate = useNavigate()
  const { carritos, cambiarCantidad, quitar, vaciar } = useCarrito()
  const [sedes, setSedes] = useState([])
  const [direcciones, setDirecciones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [sedeElegida, setSedeElegida] = useState("")
  const [tipo, setTipo] = useState("domicilio")
  const [direccionElegida, setDireccionElegida] = useState("")
  const [metodoPago, setMetodoPago] = useState(METODOS_PAGO[0].valor)
  const [observaciones, setObservaciones] = useState("")
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState(false)

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

  const confirmar = async () => {
    if (enviando || faltaDireccion || lineas.length === 0) return

    setEnviando(true)
    setError("")

    try {
      const pedido = await crearPedido({
        sede_id: sedeId,
        canal: "web",
        tipo,
        metodo_pago: metodoPago,
        observaciones: observaciones.trim(),
        detalles: detallesDePedido(lineas),
        ...(tipo === "domicilio" ? datosDeEntrega(direccion) : {}),
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

      <div className="flex items-center justify-between border-t border-borde pt-4">
        <span className="text-base font-semibold text-texto">Subtotal</span>
        <span className="font-titulo text-2xl font-semibold text-acento">{moneda(subtotal)}</span>
      </div>

      <Boton grande anchoCompleto disabled={enviando || cargando || faltaDireccion} onClick={confirmar}>
        {enviando ? "Confirmando…" : "Confirmar pedido"}
      </Boton>
    </ClienteLayout>
  )
}
