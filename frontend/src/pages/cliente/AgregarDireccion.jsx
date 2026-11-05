import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import Interruptor from "../../components/Interruptor"
import MapaDireccion from "../../components/MapaDireccion"
import MensajeAlerta from "../../components/MensajeAlerta"
import ModalAviso from "../../components/ModalAviso"
import { Lupa, UbicacionPin } from "../../components/Iconos"
import { iconoBolsaRoja } from "../../assets"
import { COBERTURA, estaEnCobertura } from "../../data/cobertura"
import { DIRECCIONES } from "../../data/direcciones"

export default function AgregarDireccion() {
  const navigate = useNavigate()
  const { id } = useParams()
  const existente = id ? DIRECCIONES.find((d) => d.id === Number(id)) : null

  const [posicion, setPosicion] = useState(COBERTURA.centro)
  const [elegida, setElegida] = useState(false)
  const [usarUbicacion, setUsarUbicacion] = useState(false)
  const [principal, setPrincipal] = useState(false)
  const [fueraDeCobertura, setFueraDeCobertura] = useState(false)
  const [errorUbicacion, setErrorUbicacion] = useState("")

  const seleccionar = (nuevaPosicion) => {
    if (!estaEnCobertura(nuevaPosicion)) {
      setFueraDeCobertura(true)
      return false
    }
    setPosicion(nuevaPosicion)
    setElegida(true)
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

  const guardar = (e) => {
    e.preventDefault()
    navigate("/cliente/direcciones")
  }

  const linea1 = elegida ? "Ubicación seleccionada" : (existente?.direccion ?? "Calle 5 # 38 - 20")
  const linea2 = elegida
    ? `${posicion[0].toFixed(5)}, ${posicion[1].toFixed(5)}`
    : "Tequendama, Cali."

  return (
    <ClienteLayout
      titulo={id ? "Editar dirección" : "Agregar dirección"}
      volverA="/cliente/direcciones"
      derecha={
        iconoBolsaRoja && (
          <img src={iconoBolsaRoja} alt="DomiPedidosX" className="h-[38px] w-[38px] object-cover" />
        )
      }
      pie={
        <Boton type="submit" form="form-direccion" grande anchoCompleto>
          Guardar dirección
        </Boton>
      }
    >
      <form id="form-direccion" onSubmit={guardar} className="-mt-7 flex flex-col gap-4">
        <label className="flex h-9 items-center gap-2 rounded-full bg-borde px-4">
          <Lupa className="h-5 w-5 shrink-0 text-primario" />
          <input
            type="search"
            aria-label="Buscar dirección"
            placeholder="Buscar dirección"
            className="w-full bg-transparent text-sm text-texto outline-none placeholder:text-texto-sec"
          />
        </label>

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
            <p className="text-base font-semibold text-black">{linea1}</p>
            <p className="text-sm text-black">{linea2}</p>
          </div>
        </div>

        <CampoTexto etiqueta="Complemento" placeholder="apto, torre, casa" />
        <CampoTexto etiqueta="Indicaciones adicionales" placeholder="Escribe aquí" />

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