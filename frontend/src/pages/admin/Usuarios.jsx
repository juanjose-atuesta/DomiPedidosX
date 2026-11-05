import { useState } from "react"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoTexto from "../../components/CampoTexto"
import ModalConfirmacion from "../../components/ModalConfirmacion"
import { useNavigate } from "react-router-dom"

const USUARIOS = [
  { id: 1, nombre: "Laura Gómez", correo: "laura@correo.com", rol: "Cocinero", sede: "Sede Centro" },
  { id: 2, nombre: "Andrés Ruiz", correo: "andres@correo.com", rol: "Operador", sede: "Sede Norte" },
  { id: 3, nombre: "Mateo Silva", correo: "mateo@correo.com", rol: "Cliente", sede: "—" },
]

const COLUMNAS = "grid grid-cols-[1fr_1.2fr_0.7fr_0.8fr_290px] items-center gap-4"
const TITULOS = ["Nombre", "Correo", "Rol", "Sede", "Acciones"]

export default function Usuarios() {
  const [modal, setModal] = useState(null)
  const cerrar = () => setModal(null)
  const navigate = useNavigate()

  return (
    <AdminLayout titulo="Usuarios" accion={<Boton onClick={() => navigate("/admin/usuarios/nueva")}>Crear cuenta de personal</Boton>}>
      <div className="overflow-x-auto rounded-xl border border-borde bg-white p-4">
        <div className="min-w-[860px]">
          <div className={`${COLUMNAS} py-3 text-xs leading-4 text-texto-sec`}>
            {TITULOS.map((t) => (
              <p key={t}>{t}</p>
            ))}
          </div>

          {USUARIOS.map((u) => (
            <div key={u.id} className={`${COLUMNAS} py-3 text-sm leading-5 text-texto`}>
              <p>{u.nombre}</p>
              <p>{u.correo}</p>
              <p>{u.rol}</p>
              <p>{u.sede}</p>
              <div className="flex items-center gap-2">
                {u.rol !== "Cliente" && (
                  <Boton tipo="secundario" onClick={() => setModal({ tipo: "rol", usuario: u })}>
                    Cambiar rol
                  </Boton>
                )}
                <Boton tipo="secundario" onClick={() => setModal({ tipo: "desactivar", usuario: u })}>
                  Desactivar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ModalConfirmacion
        abierto={modal?.tipo === "desactivar"}
        titulo="¿Desactivar cuenta?"
        texto="El cliente ya no podrá iniciar sesión. Su historial y sus pedidos en curso se conservan."
        textoConfirmar="Desactivar"
        onConfirmar={cerrar}
        onCancelar={cerrar}
      />

      <ModalConfirmacion
        abierto={modal?.tipo === "rol"}
        titulo="Cambiar rol"
        texto="El nuevo rol se aplicará en el próximo inicio de sesión de la persona."
        textoConfirmar="Guardar rol"
        onConfirmar={cerrar}
        onCancelar={cerrar}
      >
        <CampoTexto etiqueta="Nuevo rol" placeholder="Seleccionar ⌄" />
      </ModalConfirmacion>
    </AdminLayout>
  )
}