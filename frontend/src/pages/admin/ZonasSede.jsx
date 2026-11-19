import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import MapaZonas from "../../components/MapaZonas"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { actualizarZona, crearZona, desactivarZona, listarZonas } from "../../api/cobertura"
import { obtenerSede } from "../../api/sedes"
import { CENTRO_MAPA } from "../../data/cobertura"
import { mensajeDeError } from "../../utils/errores"
import { moneda } from "../../utils/formato"

const TIPOS = [
  { valor: "radio", etiqueta: "Radio desde un punto" },
  { valor: "poligono", etiqueta: "Polígono (dibujar en el mapa)" },
]
const MINIMO_PUNTOS = 3
const DECIMALES = 6

const FORMULARIO_VACIO = {
  id: null,
  nombre: "",
  tipo: "radio",
  centro: null,
  radioKm: "3",
  puntos: [],
  tarifa: "",
  pedidoMinimo: "0",
  tiempo: "30",
}

// API -> forma que usan el mapa y el formulario.
function aFormulario(zona) {
  return {
    id: zona.id,
    nombre: zona.nombre,
    tipo: zona.tipo,
    centro: zona.centro_lat != null ? [Number(zona.centro_lat), Number(zona.centro_lng)] : null,
    radioKm: zona.radio_km ?? "3",
    puntos: zona.poligono ?? [],
    tarifa: String(Number(zona.tarifa_domicilio)),
    pedidoMinimo: String(Number(zona.pedido_minimo)),
    tiempo: String(zona.tiempo_estimado_min),
  }
}

function aFigura(formulario) {
  return {
    id: formulario.id ?? "nueva",
    tipo: formulario.tipo,
    centro: formulario.centro,
    radioKm: Number(formulario.radioKm) || 0,
    puntos: formulario.puntos,
  }
}

function aPeticion(f) {
  const base = {
    nombre: f.nombre.trim(),
    tipo: f.tipo,
    tarifa_domicilio: f.tarifa || "0",
    pedido_minimo: f.pedidoMinimo || "0",
    tiempo_estimado_min: Number(f.tiempo),
  }
  if (f.tipo === "radio") {
    return {
      ...base,
      centro_lat: f.centro?.[0].toFixed(DECIMALES) ?? null,
      centro_lng: f.centro?.[1].toFixed(DECIMALES) ?? null,
      radio_km: f.radioKm,
      poligono: null,
    }
  }
  return { ...base, poligono: f.puntos, centro_lat: null, centro_lng: null, radio_km: null }
}

function geometriaLista(f) {
  return f.tipo === "radio" ? Boolean(f.centro) && Number(f.radioKm) > 0 : f.puntos.length >= MINIMO_PUNTOS
}

export default function ZonasSede() {
  const { id: sedeId } = useParams()
  const navigate = useNavigate()
  const [sede, setSede] = useState(null)
  const [zonas, setZonas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [formulario, setFormulario] = useState(null)
  const [aDesactivar, setADesactivar] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState("")
  const [mensaje, setMensaje] = useState("")

  useEffect(() => {
    let vigente = true
    Promise.all([obtenerSede(sedeId), listarZonas(sedeId)])
      .then(([datosSede, datosZonas]) => {
        if (!vigente) return
        setSede(datosSede)
        setZonas(datosZonas)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar las zonas."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [sedeId])

  const centro =
    sede?.latitud != null ? [Number(sede.latitud), Number(sede.longitud)] : CENTRO_MAPA
  const activas = zonas.filter((z) => z.activa && z.id !== formulario?.id).map((z) => aFigura(aFormulario(z)))

  const cambiar = (campo) => (e) => setFormulario((f) => ({ ...f, [campo]: e.target.value }))

  const clicMapa = (punto) => {
    if (!formulario) return
    setFormulario((f) =>
      f.tipo === "radio" ? { ...f, centro: punto } : { ...f, puntos: [...f.puntos, punto] },
    )
  }

  const guardar = async (e) => {
    e.preventDefault()
    if (guardando || !geometriaLista(formulario)) return
    setGuardando(true)
    setError("")
    setMensaje("")
    try {
      const datos = aPeticion(formulario)
      const guardada = formulario.id
        ? await actualizarZona(formulario.id, datos)
        : await crearZona(sedeId, datos)
      setZonas((actuales) =>
        formulario.id ? actuales.map((z) => (z.id === guardada.id ? guardada : z)) : [...actuales, guardada],
      )
      setMensaje(`Zona "${guardada.nombre}" guardada.`)
      setFormulario(null)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar la zona."))
    } finally {
      setGuardando(false)
    }
  }

  const reactivar = async (zona) => {
    try {
      const actualizada = await actualizarZona(zona.id, { activa: true })
      setZonas((actuales) => actuales.map((z) => (z.id === actualizada.id ? actualizada : z)))
      setMensaje(`Zona "${zona.nombre}" reactivada.`)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo reactivar la zona."))
    }
  }

  const confirmarDesactivar = async () => {
    if (!aDesactivar || guardando) return
    setGuardando(true)
    try {
      await desactivarZona(aDesactivar.id)
      setZonas((actuales) => actuales.map((z) => (z.id === aDesactivar.id ? { ...z, activa: false } : z)))
      setMensaje(`Zona "${aDesactivar.nombre}" desactivada.`)
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo desactivar la zona."))
    } finally {
      setADesactivar(null)
      setGuardando(false)
    }
  }

  return (
    <AdminLayout
      titulo={sede ? `Zonas de cobertura · ${sede.nombre}` : "Zonas de cobertura"}
      accion={
        <Boton tipo="texto" onClick={() => navigate("/admin/sedes")}>
          ← Volver
        </Boton>
      }
    >
      {mensaje && <MensajeAlerta tipo="exito">{mensaje}</MensajeAlerta>}
      {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

      {cargando ? (
        <MensajeAlerta tipo="info">Cargando zonas…</MensajeAlerta>
      ) : (
        <div className="grid items-start gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="flex flex-col gap-3">
            <MapaZonas
              centro={centro}
              zonas={activas}
              edicion={formulario && aFigura(formulario)}
              onClic={clicMapa}
            />
            {formulario && (
              <p className="text-sm text-texto-sec">
                {formulario.tipo === "radio"
                  ? "Toca el mapa para ubicar el centro de la zona."
                  : `Toca el mapa para agregar vértices (${formulario.puntos.length} de mínimo ${MINIMO_PUNTOS}).`}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-4">
            {formulario ? (
              <form onSubmit={guardar} className="flex flex-col gap-4 rounded-xl border border-borde bg-white p-6">
                <h2 className="font-titulo text-xl font-semibold text-texto">
                  {formulario.id ? "Editar zona" : "Nueva zona"}
                </h2>
                <CampoTexto etiqueta="Nombre" maxLength={100} value={formulario.nombre} onChange={cambiar("nombre")} required />
                <CampoSelect etiqueta="Forma" opciones={TIPOS} value={formulario.tipo} onChange={cambiar("tipo")} />
                {formulario.tipo === "radio" ? (
                  <CampoTexto
                    etiqueta="Radio (km)"
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={formulario.radioKm}
                    onChange={cambiar("radioKm")}
                    required
                  />
                ) : (
                  <div className="flex gap-2">
                    <Boton
                      tipo="secundario"
                      pequeno
                      disabled={formulario.puntos.length === 0}
                      onClick={() => setFormulario((f) => ({ ...f, puntos: f.puntos.slice(0, -1) }))}
                    >
                      Deshacer punto
                    </Boton>
                    <Boton
                      tipo="texto"
                      pequeno
                      disabled={formulario.puntos.length === 0}
                      onClick={() => setFormulario((f) => ({ ...f, puntos: [] }))}
                    >
                      Borrar todo
                    </Boton>
                  </div>
                )}
                <div className="grid gap-4 sm:grid-cols-3">
                  <CampoTexto etiqueta="Tarifa domicilio" type="number" min="0" step="100" value={formulario.tarifa} onChange={cambiar("tarifa")} required />
                  <CampoTexto etiqueta="Pedido mínimo" type="number" min="0" step="100" value={formulario.pedidoMinimo} onChange={cambiar("pedidoMinimo")} required />
                  <CampoTexto etiqueta="Tiempo (min)" type="number" min="1" max="600" value={formulario.tiempo} onChange={cambiar("tiempo")} required />
                </div>
                <div className="flex justify-end gap-3">
                  <Boton tipo="secundario" onClick={() => setFormulario(null)}>
                    Cancelar
                  </Boton>
                  <Boton type="submit" disabled={guardando || !geometriaLista(formulario)}>
                    {guardando ? "Guardando…" : "Guardar zona"}
                  </Boton>
                </div>
              </form>
            ) : (
              <Boton className="self-start" onClick={() => setFormulario({ ...FORMULARIO_VACIO, centro })}>
                Nueva zona
              </Boton>
            )}

            <div className="flex flex-col gap-2 rounded-xl border border-borde bg-white p-4">
              {zonas.length === 0 && (
                <p className="text-sm text-texto-sec">
                  Esta sede aún no tiene zonas: no recibirá pedidos a domicilio hasta que crees una.
                </p>
              )}
              {zonas.map((zona) => (
                <div key={zona.id} className="flex items-center justify-between gap-3 border-b border-borde py-2 last:border-0">
                  <div className="min-w-0 text-sm">
                    <p className={`font-semibold ${zona.activa ? "text-texto" : "text-texto-sec"}`}>
                      {zona.nombre} {!zona.activa && "(inactiva)"}
                    </p>
                    <p className="text-xs text-texto-sec">
                      {zona.tipo === "radio" ? `Radio ${Number(zona.radio_km)} km` : `Polígono de ${zona.poligono.length} puntos`}
                      {" · "}Domicilio {moneda(zona.tarifa_domicilio)} · Mínimo {moneda(zona.pedido_minimo)} ·{" "}
                      {zona.tiempo_estimado_min} min
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <Boton tipo="texto" pequeno onClick={() => setFormulario(aFormulario(zona))}>
                      Editar
                    </Boton>
                    {zona.activa ? (
                      <Boton tipo="texto" pequeno onClick={() => setADesactivar(zona)}>
                        Desactivar
                      </Boton>
                    ) : (
                      <Boton tipo="texto" pequeno onClick={() => reactivar(zona)}>
                        Reactivar
                      </Boton>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <ModalConfirmacion
        abierto={Boolean(aDesactivar)}
        titulo="¿Desactivar zona?"
        texto="Las direcciones de esta zona dejarán de recibir domicilios de la sede. Los pedidos ya hechos se conservan."
        textoConfirmar={guardando ? "Desactivando…" : "Desactivar"}
        onConfirmar={confirmarDesactivar}
        onCancelar={() => setADesactivar(null)}
      />
    </AdminLayout>
  )
}
