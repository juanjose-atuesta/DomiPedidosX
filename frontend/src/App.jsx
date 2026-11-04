import { useState } from "react"
import Boton from "./components/Boton"
import ChipCategoria from "./components/ChipCategoria"
import MensajeAlerta from "./components/MensajeAlerta"
import ModalConfirmacion from "./components/ModalConfirmacion"
import TarjetaProducto from "./components/TarjetaProducto"

export default function App() {
  const [modal, setModal] = useState(false)

  return (
    <div className="space-y-8 p-8">
      <div className="flex gap-2">
        <ChipCategoria activo>Todas</ChipCategoria>
        <ChipCategoria>Hamburguesas</ChipCategoria>
        <ChipCategoria>Bebidas</ChipCategoria>
      </div>

      <div className="flex max-w-md flex-col gap-3">
        <MensajeAlerta tipo="exito">Sede creada correctamente</MensajeAlerta>
        <MensajeAlerta tipo="error">Ya existe una sede con ese nombre</MensajeAlerta>
        <MensajeAlerta tipo="aviso">Papas fritas y Brownie están en su stock mínimo.</MensajeAlerta>
        <MensajeAlerta tipo="info">El rol define a qué módulo podrá entrar esta persona.</MensajeAlerta>
      </div>

      <div className="flex gap-4">
        <TarjetaProducto nombre="Hamburguesa clásica" descripcion="Carne, queso y vegetales" tiempo={15} precio={18000} />
        <TarjetaProducto nombre="Limonada de coco" descripcion="Refrescante y natural" tiempo={5} precio={9000} agotado />
      </div>

      <Boton onClick={() => setModal(true)}>Desactivar sede</Boton>
      <ModalConfirmacion
        abierto={modal}
        titulo="¿Desactivar sede?"
        texto="La sede dejará de recibir pedidos nuevos. Los pedidos en curso se terminan normalmente y su historial se conserva."
        textoConfirmar="Desactivar"
        onConfirmar={() => setModal(false)}
        onCancelar={() => setModal(false)}
      />
    </div>
  )
}