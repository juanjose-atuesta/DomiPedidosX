import { useEffect, useState } from "react"
import { listarSedes } from "../api/sedes"
import { useAuth } from "../context/auth-context"
import { ROLES, normalizarRol } from "../utils/roles"
import { mensajeDeError } from "../utils/errores"

// Sedes en las que trabaja el usuario: el admin todas las activas, el resto las asignadas.
export function useSedesUsuario() {
  const { usuario } = useAuth()
  const esAdmin = normalizarRol(usuario?.rol) === ROLES.ADMIN
  const [sedesAdmin, setSedesAdmin] = useState([])
  const [cargando, setCargando] = useState(esAdmin)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!esAdmin) return undefined
    let vigente = true

    listarSedes()
      .then((datos) => {
        if (vigente) setSedesAdmin(datos)
      })
      .catch((err) => {
        if (vigente) setError(mensajeDeError(err, "No se pudieron cargar las sedes."))
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [esAdmin])

  return {
    esAdmin,
    sedes: esAdmin ? sedesAdmin : (usuario?.sedes ?? []),
    cargando,
    error,
  }
}
