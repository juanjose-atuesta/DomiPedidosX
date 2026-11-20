const ETIQUETAS_CAMPO = {
  nombre: "Nombre",
  apellido: "Apellido",
  email: "Correo electrónico",
  telefono: "Teléfono",
  password: "Contraseña",
  password_confirmacion: "Confirmación de contraseña",
  rol: "Rol",
  sedes_ids: "Sedes",
  direccion: "Dirección",
  latitud: "Latitud",
  longitud: "Longitud",
  horarios: "Horarios",
  dia_semana: "Día",
  hora_apertura: "Hora de apertura",
  hora_cierre: "Hora de cierre",
  detail: "",
  error: "",
  non_field_errors: "",
}

function etiquetaCampo(campo) {
  return ETIQUETAS_CAMPO[campo] ?? campo
}

function extraerMensajes(valor, campo = "") {
  if (valor == null) return []

  if (typeof valor === "string") {
    const etiqueta = etiquetaCampo(campo)
    return [etiqueta ? `${etiqueta}: ${valor}` : valor]
  }

  if (Array.isArray(valor)) {
    return valor.flatMap((item) => extraerMensajes(item, campo))
  }

  if (typeof valor === "object") {
    if (typeof valor.detail === "string") return [valor.detail]

    return Object.entries(valor).flatMap(([clave, contenido]) =>
      extraerMensajes(contenido, clave),
    )
  }

  return [String(valor)]
}

export function mensajeDeError(error, alternativo = "Ocurrió un error inesperado.") {
  if (!error?.response) {
    if (error?.code === "ERR_NETWORK") {
      return "No se pudo conectar con el servidor. Verifica que el backend esté en ejecución."
    }
    return error?.message || alternativo
  }

  const datos = error.response.data
  if (!datos) return alternativo

  if (typeof datos === "string") return datos

  const mensajes = extraerMensajes(datos)
  return mensajes.length ? mensajes.join(" ") : alternativo
}
