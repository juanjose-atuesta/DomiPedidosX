import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import ClienteLayout from "../../layouts/ClienteLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { Candado } from "../../components/Iconos"
import { fondoPerfil, iconoBolsaNaranja } from "../../assets"

const FONDO = {
  backgroundImage: `${fondoPerfil ? `url(${fondoPerfil}), ` : ""}linear-gradient(to bottom, #ffffff, #fce3c8)`,
  backgroundSize: "100% 100%",
  backgroundPosition: "top center",
  backgroundAttachment: "fixed",
}

export default function Perfil() {
  const navigate = useNavigate()
  const entradaFoto = useRef(null)
  const [foto, setFoto] = useState(null)
  const [nombre, setNombre] = useState("Juan")
  const [apellido, setApellido] = useState("Pérez")
  const [telefono, setTelefono] = useState("300 123 4567")
  const [eliminando, setEliminando] = useState(false)

  useEffect(() => {
    return () => {
      if (foto) URL.revokeObjectURL(foto)
    }
  }, [foto])

  const elegirFoto = (archivo) => {
    if (!archivo || !archivo.type.startsWith("image/")) return
    setFoto(URL.createObjectURL(archivo))
  }

  const guardar = (e) => {
    e.preventDefault()
  }

  return (
    <ClienteLayout
      titulo="Mi perfil"
      barra
      fondo={FONDO}
      derecha={
        iconoBolsaNaranja && (
          <img src={iconoBolsaNaranja} alt="DomiPedidosX" className="h-[38px] w-[38px] object-cover" />
        )
      }
    >
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-32 w-32 items-center justify-center overflow-hidden rounded-full bg-fondo font-titulo text-[56px] font-semibold text-ambar">
          {foto ? (
            <img src={foto} alt="Tu foto de perfil" className="h-full w-full object-cover" />
          ) : (
            nombre.charAt(0).toUpperCase() || "?"
          )}
        </div>
        <Boton tipo="ambar" pequeno onClick={() => entradaFoto.current?.click()}>
          Editar imagen
        </Boton>
        <input
          ref={entradaFoto}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => elegirFoto(e.target.files[0])}
        />
      </div>

      <form onSubmit={guardar} className="flex flex-col gap-4">
        <CampoTexto
          etiqueta="Nombre*"
          placeholder="Escribe aquí"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <CampoTexto
          etiqueta="Apellido*"
          placeholder="Escribe aquí"
          value={apellido}
          onChange={(e) => setApellido(e.target.value)}
          required
        />
        <div className="relative">
          <CampoTexto etiqueta="Correo electrónico*" defaultValue="juan123@gmail.com" disabled />
          <Candado className="absolute bottom-[14px] right-4 h-5 w-5 text-texto-sec" />
        </div>
        <CampoTexto
          etiqueta="Teléfono móvil*"
          type="tel"
          placeholder="Escribe aquí"
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
          required
        />
        <Boton type="submit" tipo="ambar" className="w-[249px] self-center">
          Guardar cambios
        </Boton>
      </form>

      <div className="flex flex-col items-center gap-4 pb-4">
        <Boton tipo="secundario" onClick={() => navigate("/login")}>
          Cerrar sesión
        </Boton>
        <button
          type="button"
          onClick={() => setEliminando(true)}
          className="text-base font-semibold text-primario hover:underline"
        >
          Eliminar cuenta
        </button>
      </div>


      <ModalConfirmacion
        abierto={eliminando}
        titulo="¿Eliminar cuenta?"
        texto="Se eliminarán tus datos personales y tus direcciones guardadas. Esta acción no se puede deshacer."
        textoConfirmar="Eliminar cuenta"
        onConfirmar={() => setEliminando(false)}
        onCancelar={() => setEliminando(false)}
      />
    </ClienteLayout>
  )
}