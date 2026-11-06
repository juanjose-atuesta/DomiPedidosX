export const ROLES = {
  ADMIN: "admin",
  OPERADOR: "operador",
  COCINA: "cocina",
  REPARTIDOR: "repartidor",
  CLIENTE: "cliente",
}

export const ETIQUETAS_ROL = {
  [ROLES.ADMIN]: "Administrador",
  [ROLES.OPERADOR]: "Operador de sede",
  [ROLES.COCINA]: "Cocina",
  [ROLES.REPARTIDOR]: "Repartidor",
  [ROLES.CLIENTE]: "Cliente",
}

export const OPCIONES_ROL_PERSONAL = [
  { valor: ROLES.OPERADOR, etiqueta: ETIQUETAS_ROL[ROLES.OPERADOR] },
  { valor: ROLES.COCINA, etiqueta: ETIQUETAS_ROL[ROLES.COCINA] },
  { valor: ROLES.REPARTIDOR, etiqueta: ETIQUETAS_ROL[ROLES.REPARTIDOR] },
  { valor: ROLES.ADMIN, etiqueta: ETIQUETAS_ROL[ROLES.ADMIN] },
]

export const OPCIONES_ROL = Object.entries(ETIQUETAS_ROL).map(
  ([valor, etiqueta]) => ({ valor, etiqueta }),
)

export const INICIO_POR_ROL = {
  [ROLES.ADMIN]: "/admin/usuarios",
  [ROLES.OPERADOR]: "/operador/productos",
  [ROLES.COCINA]: "/cocina",
  [ROLES.REPARTIDOR]: "/repartidor",
  [ROLES.CLIENTE]: "/cliente",
}

// Roles que entran a cada sección de la app; App.jsx protege sus rutas con esta tabla.
export const ROLES_POR_SECCION = {
  "/admin": [ROLES.ADMIN],
  "/operador": [ROLES.OPERADOR, ROLES.ADMIN],
  "/cocina": [ROLES.COCINA, ROLES.OPERADOR, ROLES.ADMIN],
  "/repartidor": [ROLES.REPARTIDOR],
  "/cliente": [ROLES.CLIENTE],
}

export function normalizarRol(rol) {
  return String(rol ?? "").toLowerCase()
}

export function etiquetaRol(rol) {
  const normalizado = normalizarRol(rol)
  return ETIQUETAS_ROL[normalizado] ?? rol ?? ""
}

export function rutaInicio(rol) {
  return INICIO_POR_ROL[normalizarRol(rol)] ?? "/panel-no-disponible"
}

export function tieneRol(usuario, roles) {
  if (!roles || roles.length === 0) return true
  return roles.map(normalizarRol).includes(normalizarRol(usuario?.rol))
}

// Evita volver tras el ingreso a una ruta que pertenece a otro rol.
export function puedeEntrarA(rol, ruta) {
  const seccion = Object.keys(ROLES_POR_SECCION).find(
    (s) => ruta === s || ruta.startsWith(`${s}/`),
  )
  return Boolean(seccion) && tieneRol({ rol }, ROLES_POR_SECCION[seccion])
}
