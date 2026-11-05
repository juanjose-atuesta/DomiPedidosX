import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"

export default function CrearCuentaPersonal() {
  const navigate = useNavigate()
  const volver = () => navigate("/admin/usuarios")

  const guardar = (e) => {
    e.preventDefault()
    volver()
  }

  return (
    <AdminLayout
      titulo="Crear cuenta de personal"
      accion={<Boton tipo="texto" onClick={volver}>← Volver</Boton>}
    >
      <div className="flex flex-wrap items-start gap-6">
        <form
          onSubmit={guardar}
          className="flex w-full max-w-[704px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto etiqueta="Nombre completo" placeholder="Escribe aquí" required />
            <CampoTexto etiqueta="Correo electrónico" type="email" placeholder="Escribe aquí" required />
            <CampoTexto etiqueta="Contraseña temporal" type="password" placeholder="Escribe aquí" required />
            <CampoSelect etiqueta="Rol" opciones={["Operador de sede", "Cocinero", "Repartidor"]} />
            <CampoSelect etiqueta="Sede" opciones={["Sede Centro", "Sede Norte", "Sede Sur"]} />
          </div>

          <MensajeAlerta tipo="info">
            El rol define a qué módulo podrá entrar esta persona
          </MensajeAlerta>

          <div className="flex justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>Cancelar</Boton>
            <Boton type="submit">Crear cuenta</Boton>
          </div>
        </form>

        <aside className="flex w-full max-w-[320px] flex-col gap-3 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
            Roles y accesos
          </h2>
          <p className="text-base">
            <strong className="font-semibold">Operador de sede:</strong>{" "}
            <span className="text-texto-sec">gestiona el menú, el inventario y los pedidos de su sede</span>
          </p>
          <p className="text-base">
            <strong className="font-semibold">Cocinero:</strong>{" "}
            <span className="text-texto-sec">ve el tablero de cocina y avanza los pedidos</span>
          </p>
          <p className="text-base">
            <strong className="font-semibold">Repartidor:</strong>{" "}
            <span className="text-texto-sec">ve sus pedidos asignados y registra las entregas</span>
          </p>
        </aside>
      </div>
    </AdminLayout>
  )
}