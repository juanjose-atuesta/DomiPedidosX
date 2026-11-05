import { useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { SEDES, formatearHora } from "../../data/sedes"

const COLUMNAS = "grid grid-cols-[1fr_1.2fr_1.3fr_0.7fr_290px] items-center gap-4"
const TITULOS = ["Nombre", "Dirección", "Horario", "Estado", "Acciones"]

export default function Sedes() {
  const navigate = useNavigate()
  const [sedeADesactivar, setSedeADesactivar] = useState(null)
  const cerrar = () => setSedeADesactivar(null)

  return (
    <AdminLayout
      titulo="Sedes"
      accion={<Boton onClick={() => navigate("/admin/sedes/nueva")}>Nueva sede</Boton>}
    >
      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[900px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {SEDES.map((s) => (
            <div key={s.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
              <p>{s.nombre}</p>
              <p>{s.direccion}</p>
              <p>
                {formatearHora(s.apertura)} - {formatearHora(s.cierre)}
              </p>
              <p className={s.activa ? "text-exito" : "text-texto-sec"}>
                {s.activa ? "Activa" : "Inactiva"}
              </p>
              <div className="flex items-center gap-2">
                <Boton tipo="secundario" onClick={() => navigate(`/admin/sedes/${s.id}/editar`)}>
                  Editar
                </Boton>
                <Boton
                  tipo="secundario"
                  disabled={!s.activa}
                  onClick={() => setSedeADesactivar(s)}
                >
                  Desactivar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ModalConfirmacion
        abierto={Boolean(sedeADesactivar)}
        titulo="¿Desactivar sede?"
        texto="La sede dejará de recibir pedidos nuevos. Los pedidos en curso se terminan normalmente y su historial se conserva."
        textoConfirmar="Desactivar"
        onConfirmar={cerrar}
        onCancelar={cerrar}
      />
    </AdminLayout>
  )
}