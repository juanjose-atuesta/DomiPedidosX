import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"
import CampoSelect from "../../components/CampoSelect"
import CampoTexto from "../../components/CampoTexto"
import MensajeAlerta from "../../components/MensajeAlerta"
import { listarSedes } from "../../api/sedes"
import { crearPersonal } from "../../api/usuarios"
import { mensajeDeError } from "../../utils/errores"
import { OPCIONES_ROL_PERSONAL, ROLES } from "../../utils/roles"

const FORMULARIO_VACIO = {
  nombre: "",
  apellido: "",
  telefono: "",
  email: "",
  password: "",
  password_confirmacion: "",
  rol: ROLES.OPERADOR,
}

export default function CrearCuentaPersonal() {
  const navigate = useNavigate()
  const [formulario, setFormulario] = useState(FORMULARIO_VACIO)
  const [sedes, setSedes] = useState([])
  const [sedesSeleccionadas, setSedesSeleccionadas] = useState([])
  const [cargandoSedes, setCargandoSedes] = useState(true)
  const [errorSedes, setErrorSedes] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState("")

  const volver = () => navigate("/admin/usuarios")

  useEffect(() => {
    let vigente = true

    listarSedes()
      .then((datos) => {
        if (vigente) setSedes(datos)
      })
      .catch((err) => {
        if (vigente) {
          setErrorSedes(
            mensajeDeError(err, "No se pudieron cargar las sedes activas."),
          )
        }
      })
      .finally(() => {
        if (vigente) setCargandoSedes(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const actualizarCampo = (campo) => (evento) => {
    setFormulario((actual) => ({ ...actual, [campo]: evento.target.value }))
  }

  const alternarSede = (sedeId) => {
    setSedesSeleccionadas((actuales) =>
      actuales.includes(sedeId)
        ? actuales.filter((id) => id !== sedeId)
        : [...actuales, sedeId],
    )
  }

  const guardar = async (evento) => {
    evento.preventDefault()
    setError("")

    if (formulario.password !== formulario.password_confirmacion) {
      setError("Las contraseñas no coinciden.")
      return
    }

    if (
      formulario.rol !== ROLES.ADMIN &&
      sedesSeleccionadas.length === 0
    ) {
      setError("Debes asignar al menos una sede para este rol.")
      return
    }

    setEnviando(true)

    try {
      await crearPersonal({
        nombre: formulario.nombre.trim(),
        apellido: formulario.apellido.trim(),
        telefono: formulario.telefono.trim(),
        email: formulario.email.trim(),
        password: formulario.password,
        password_confirmacion: formulario.password_confirmacion,
        rol: formulario.rol,
        sedes_ids: sedesSeleccionadas,
      })

      navigate("/admin/usuarios", {
        state: { mensaje: "Cuenta de personal creada correctamente." },
      })
    } catch (err) {
      setError(
        mensajeDeError(err, "No se pudo crear la cuenta de personal."),
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <AdminLayout
      titulo="Crear cuenta de personal"
      accion={
        <Boton tipo="texto" onClick={volver}>
          ← Volver
        </Boton>
      }
    >
      <div className="flex flex-wrap items-start gap-6">
        <form
          onSubmit={guardar}
          className="flex w-full max-w-[704px] flex-col gap-4 rounded-xl border border-borde bg-white p-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <CampoTexto
              etiqueta="Nombre"
              placeholder="Escribe aquí"
              value={formulario.nombre}
              onChange={actualizarCampo("nombre")}
              required
            />
            <CampoTexto
              etiqueta="Apellido"
              placeholder="Escribe aquí"
              value={formulario.apellido}
              onChange={actualizarCampo("apellido")}
              required
            />
            <CampoTexto
              etiqueta="Correo electrónico"
              type="email"
              placeholder="Escribe aquí"
              value={formulario.email}
              onChange={actualizarCampo("email")}
              required
            />
            <CampoTexto
              etiqueta="Teléfono"
              type="tel"
              placeholder="Escribe aquí"
              value={formulario.telefono}
              onChange={actualizarCampo("telefono")}
              required
            />
            <CampoTexto
              etiqueta="Contraseña temporal"
              type="password"
              placeholder="Escribe aquí"
              value={formulario.password}
              onChange={actualizarCampo("password")}
              required
            />
            <CampoTexto
              etiqueta="Confirmar contraseña temporal"
              type="password"
              placeholder="Escribe aquí"
              value={formulario.password_confirmacion}
              onChange={actualizarCampo("password_confirmacion")}
              required
            />
            <CampoSelect
              etiqueta="Rol"
              opciones={OPCIONES_ROL_PERSONAL}
              value={formulario.rol}
              onChange={actualizarCampo("rol")}
            />
          </div>

          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm text-texto">Sedes asignadas</legend>
            {cargandoSedes ? (
              <p className="text-sm text-texto-sec">Cargando sedes…</p>
            ) : sedes.length === 0 ? (
              <p className="text-sm text-texto-sec">
                No hay sedes activas. Crea una sede antes de asignar personal
                operativo.
              </p>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {sedes.map((sede) => (
                  <label
                    key={sede.id}
                    className="flex items-center gap-2 rounded-lg border border-borde bg-white px-3 py-2 text-sm text-texto"
                  >
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-primario"
                      checked={sedesSeleccionadas.includes(sede.id)}
                      onChange={() => alternarSede(sede.id)}
                    />
                    <span>{sede.nombre}</span>
                  </label>
                ))}
              </div>
            )}
            <p className="text-xs text-texto-sec">
              Los roles operativos requieren al menos una sede. El
              administrador puede no tener sedes asignadas.
            </p>
          </fieldset>

          {errorSedes && <MensajeAlerta tipo="error">{errorSedes}</MensajeAlerta>}

          <MensajeAlerta tipo="info">
            El rol define a qué módulo podrá entrar esta persona.
          </MensajeAlerta>

          {error && <MensajeAlerta tipo="error">{error}</MensajeAlerta>}

          <div className="flex justify-end gap-3 py-[10px]">
            <Boton tipo="secundario" onClick={volver}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={enviando}>
              {enviando ? "Creando cuenta…" : "Crear cuenta"}
            </Boton>
          </div>
        </form>

        <aside className="flex w-full max-w-[320px] flex-col gap-3 rounded-xl border border-borde bg-white p-6">
          <h2 className="font-titulo text-[28px] font-semibold leading-9 text-texto">
            Roles y accesos
          </h2>
          <p className="text-base">
            <strong className="font-semibold">Operador de sede:</strong>{" "}
            <span className="text-texto-sec">
              gestiona el menú, el inventario y los pedidos de su sede
            </span>
          </p>
          <p className="text-base">
            <strong className="font-semibold">Cocina:</strong>{" "}
            <span className="text-texto-sec">
              ve el tablero de cocina y avanza los pedidos
            </span>
          </p>
          <p className="text-base">
            <strong className="font-semibold">Repartidor:</strong>{" "}
            <span className="text-texto-sec">
              ve sus pedidos asignados y registra las entregas
            </span>
          </p>
          <p className="text-base">
            <strong className="font-semibold">Administrador:</strong>{" "}
            <span className="text-texto-sec">
              administra sedes, usuarios y la configuración general
            </span>
          </p>
        </aside>
      </div>
    </AdminLayout>
  )
}
