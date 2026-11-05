import { useNavigate, useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import CampoSelect from "../../components/CampoSelect"
import MensajeAlerta from "../../components/MensajeAlerta"
import EtiquetaEstado from "../../components/EtiquetaEstado"
import { SEDES } from "../../data/sedes"

export default function FormularioSede() {
  const navigate = useNavigate()
  const { id } = useParams()
  const sede = id ? SEDES.find((s) => s.id === Number(id)) : null
  const volver = () => navigate("/admin/sedes")

  const guardar = (e) => {
    e.preventDefault()
    volver()
  }

  return (
    <AdminLayout
      titulo={id ? "Editar sede" : "Nueva sede"}
      accion={<Boton tipo="texto" onClick={volver}>← Volver</Boton>}
    >
      <div className="flex flex-wrap items-start gap-6">
        <form
          onSubmit={guardar}
          className="flex w-full max-w-[704px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto etiqueta="Nombre de la sede" placeholder="Escribe aquí" defaultValue={sede?.nombre} required />
            <CampoTexto etiqueta="Teléfono" type="tel" placeholder="Escribe aquí" defaultValue={sede?.telefono} required />
            <CampoTexto etiqueta="Dirección" placeholder="Escribe aquí" defaultValue={sede?.direccion} required />
            <CampoSelect etiqueta="Ciudad" opciones={["Cali", "Jamundí", "Palmira", "Yumbo"]} defaultValue={sede?.ciudad} />
            <CampoTexto etiqueta="Hora de apertura" type="time" defaultValue={sede?.apertura} required />
            <CampoTexto etiqueta="Hora de cierre" type="time" defaultValue={sede?.cierre} required />
          </div>

          <MensajeAlerta tipo="info">
            La sede solo recibirá pedidos dentro de este horario
          </MensajeAlerta>

          <div className="flex justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>Cancelar</Boton>
            <Boton type="submit">Guardar sede</Boton>
          </div>
        </form>

        <aside className="flex w-full max-w-[320px] flex-col items-start gap-3 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
            Estado de la sede
          </h2>
          {sede && !sede.activa ? (
            <EtiquetaEstado estado="recibido">Inactiva</EtiquetaEstado>
          ) : (
            <EtiquetaEstado estado="entregado">Activa</EtiquetaEstado>
          )}
          <p className="text-base text-texto-sec">
            Podrás desactivarla desde la lista de sedes sin perder su historial
          </p>
        </aside>
      </div>
    </AdminLayout>
  )
}