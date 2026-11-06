import { useEffect, useState } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import Interruptor from "../../components/Interruptor"
import MapaDireccion from "../../components/MapaDireccion"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalAviso from "../../components/ModalAviso"
import { UbicacionPin } from "../../components/Iconos"
import { iconoBolsaRoja } from "../../assets"
import {
  actualizarDireccion,
  crearDireccion,
  listarDirecciones,
} from "../../api/direcciones"
import { COBERTURA, estaEnCobertura } from "../../data/cobertura"
import { mensajeDeError } from "../../utils/errores"

const DECIMALES_COORDENADA = 6

function Formulario({ id, existente, volverA }) {
  const navigate = useNavigate()
  const [alias, setAlias] = useState(existente?.alias ?? "")
  const [direccionTexto, setDireccionTexto] = useState(existente?.direccion_texto ?? "")
  const [detalles, setDetalles] = useState(existente?.detalles ?? "")
  const [posicion, setPosicion] = useState(
    existente ? [Number(existente.latitud), Number(existente.longitud)] : COBERTURA.centro,
  )
  const [elegida, setElegida] = useState(Boolean(existente))
  const [usarUbicacion, setUsarUbicacion] = useState(false)
  const [principal, setPrincipal] = useState(existente?.es_principal ?? false)
  const [fueraDeCobertura, setFueraDeCobertura] = useState(false)
  const [errorUbicacion, setErrorUbicacion] = useState("")
  const [error, setError] = useState("")
  const [guardando, setGuardando] = useState(false)

  const seleccionar = (nuevaPosicion) => {
    if (!estaEnCobertura(nuevaPosicion)) {
      setFueraDeCobertura(true)
      return false
    }
    setPosicion(nuevaPosicion)
    setElegida(true)
    setError("")
    return true
  }

  const alternarUbicacion = (valor) => {
    setUsarUbicacion(valor)
    setErrorUbicacion("")
    if (!valor) return

    if (!navigator.geolocation) {
      setUsarUbicacion(false)
      setErrorUbicacion("Tu navegador no permite obtener la ubicación")
      return
    }

    navigator.geolocation.getCurrentPosition(
      (p) => {
        if (!seleccionar([p.coords.latitude, p.coords.longitude])) setUsarUbicacion(false)
      },
      () => {
        setUsarUbicacion(false)
        setErrorUbicacion("No pudimos obtener tu ubicación")
      },
    )
  }

  const guardar = async (e) => {
    e.preventDefault()
    if (guardando) return
    if (!elegida) {
      setError("Toca el mapa para marcar el punto de entrega")
      return
    }

    setGuardando(true)
    setError("")
    const datos = {
      alias: alias.trim(),
      direccion_texto: direccionTexto.trim(),
      detalles: detalles.trim(),
      latitud: posicion[0].toFixed(DECIMALES_COORDENADA),
      longitud: posicion[1].toFixed(DECIMALES_COORDENADA),
      es_principal: principal,
    }

    try {
      if (id) {
        await actualizarDireccion(id, datos)
      } else {
        await crearDireccion(datos)
      }
      navigate(volverA, { replace: true })
    } catch (err) {
      setError(mensajeDeError(err, "No se pudo guardar la dirección."))
      setGuardando(false)
    }
  }

  return (
    <ClienteLayout
      titulo={id ? "Editar dirección" : "Agregar dirección"}
      volverA={volverA}
      derecha={
        iconoBolsaRoja && (
          <img src={iconoBolsaRoja} alt="DomiPedidosX" className="h-[38px] w-[38px] object-cover" />
        )
      }
      pie={
        <Boton type="submit" form="form-direccion" grande anchoCompleto disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar dirección"}
        </Boton>
      }
    >
      <form id="form-direccion" onSubmit={guardar} className="-mt-7 flex flex-col gap-4">
        {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

        <MapaDireccion posicion={posicion} onSeleccionar={seleccionar} />

        <div className="flex items-center justify-between px-[13px]">
          <span className="text-base text-texto">Usar mi ubicación actual</span>
          <Interruptor activo={usarUbicacion} onChange={alternarUbicacion} etiqueta="Usar mi ubicación actual" />
        </div>

        {errorUbicacion && <MensajeAlerta tipo="error">{errorUbicacion}</MensajeAlerta>}

        <div className="flex items-center gap-4 px-[5px]">
          <span className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[15px] bg-primario text-white">
            <UbicacionPin />
          </span>
          <div>
            <p className="text-base font-semibold text-black">
              {elegida ? "Punto de entrega marcado" : "Toca el mapa para marcar el punto"}
            </p>
            {elegida && (
              <p className="text-sm text-black">
                {posicion[0].toFixed(5)}, {posicion[1].toFixed(5)}
              </p>
            )}
          </div>
        </div>

        <CampoTexto
          etiqueta="Nombre"
          placeholder="Casa, Trabajo…"
          maxLength={50}
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
          required
        />
        <CampoTexto
          etiqueta="Dirección"
          placeholder="Calle 5 # 38 - 20"
          value={direccionTexto}
          onChange={(e) => setDireccionTexto(e.target.value)}
          required
        />
        <CampoTexto
          etiqueta="Complemento e indicaciones"
          placeholder="apto, torre, casa"
          value={detalles}
          onChange={(e) => setDetalles(e.target.value)}
        />

        <div className="flex items-center justify-between px-[5px]">
          <span className="text-base font-semibold text-primario">Usar como dirección principal</span>
          <Interruptor activo={principal} onChange={setPrincipal} etiqueta="Usar como dirección principal" />
        </div>
      </form>

      <ModalAviso
        abierto={fueraDeCobertura}
        titulo="Fuera de cobertura"
        texto="Aún no llegamos a esta zona. Prueba con otra dirección."
        onCerrar={() => setFueraDeCobertura(false)}
      />
    </ClienteLayout>
  )
}

export default function AgregarDireccion() {
  const { id } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()
  const volverA = state?.volverA ?? "/cliente/direcciones"
  const [existente, setExistente] = useState(null)
  const [estado, setEstado] = useState(id ? "cargando" : "listo")
  const [error, setError] = useState("")

  useEffect(() => {
    if (!id) return undefined
    let vigente = true

    listarDirecciones()
      .then((direcciones) => {
        if (!vigente) return
        const encontrada = direcciones.find((d) => d.id === id)
        if (encontrada) {
          setExistente(encontrada)
          setEstado("listo")
        } else {
          setError("No encontramos esta dirección.")
          setEstado("error")
        }
      })
      .catch((err) => {
        if (!vigente) return
        setError(mensajeDeError(err, "No se pudo cargar la dirección."))
        setEstado("error")
      })

    return () => {
      vigente = false
    }
  }, [id])

  if (estado === "listo") {
    return <Formulario id={id} existente={existente} volverA={volverA} />
  }

  return (
    <ClienteLayout titulo="Editar dirección" volverA={volverA}>
      <MensajeAlerta tipo={error ? "error" : "info"}>{error || "Cargando…"}</MensajeAlerta>
      {error && (
        <Boton tipo="secundario" onClick={() => navigate(volverA)}>
          Volver
        </Boton>
      )}
    </ClienteLayout>
  )
}
