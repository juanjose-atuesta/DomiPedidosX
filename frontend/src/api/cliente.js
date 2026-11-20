import axios from "axios"

const PREFIJO_ALMACENAMIENTO = "domipedidos."
const ACCESS_KEY = `${PREFIJO_ALMACENAMIENTO}access`
const REFRESH_KEY = `${PREFIJO_ALMACENAMIENTO}refresh`

function normalizarBaseUrl(url) {
  const limpio = (url || "http://localhost:8000").trim().replace(/\/+$/, "")
  return /\/api$/.test(limpio) ? limpio : `${limpio}/api`
}

export const API_URL = normalizarBaseUrl(import.meta.env.VITE_API_URL)

export function obtenerAccess() {
  return localStorage.getItem(ACCESS_KEY)
}

export function obtenerRefresh() {
  return localStorage.getItem(REFRESH_KEY)
}

export function guardarTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function limpiarTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

// Cierre de sesión: no deja rastro de la cuenta en este navegador (tokens, sede, carrito).
export function limpiarSesion() {
  Object.keys(localStorage)
    .filter((clave) => clave.startsWith(PREFIJO_ALMACENAMIENTO))
    .forEach((clave) => localStorage.removeItem(clave))
  delete api.defaults.headers.common.Authorization
}

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
})

api.interceptors.request.use((config) => {
  const access = obtenerAccess()
  // Un token viejo no debe interferir con el ingreso de otra cuenta.
  if (access && !esRutaDeAuth(config.url)) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

let promesaRefresco = null

function redirigirALogin() {
  if (typeof window === "undefined") return
  if (window.location.pathname !== "/login") {
    window.location.assign("/login")
  }
}

function esRutaDeAuth(url = "") {
  return url.includes("/auth/login/") || url.includes("/auth/refresh/")
}

api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    if (status !== 401 || !original || original._reintentado || esRutaDeAuth(original.url)) {
      return Promise.reject(error)
    }

    const refresh = obtenerRefresh()
    if (!refresh) {
      limpiarTokens()
      redirigirALogin()
      return Promise.reject(error)
    }

    original._reintentado = true

    try {
      if (!promesaRefresco) {
        promesaRefresco = axios
          .post(`${API_URL}/auth/refresh/`, { refresh })
          .then(({ data }) => {
            // Si cerró sesión mientras tanto, no se restauran los tokens.
            if (obtenerRefresh() !== refresh) throw new Error("La sesión ya no está activa.")
            guardarTokens({ access: data.access, refresh: data.refresh ?? refresh })
            return data.access
          })
          .finally(() => {
            promesaRefresco = null
          })
      }

      const access = await promesaRefresco
      original.headers.Authorization = `Bearer ${access}`
      return api.request(original)
    } catch (errorRefresco) {
      limpiarTokens()
      redirigirALogin()
      return Promise.reject(errorRefresco)
    }
  },
)

export default api
