export const ESTADOS_PEDIDO = [
  { valor: "recibido", etiqueta: "Recibido" },
  { valor: "en_preparacion", etiqueta: "En preparación" },
  { valor: "listo_despacho", etiqueta: "Listo para despacho" },
  { valor: "en_camino", etiqueta: "En camino" },
  { valor: "entregado", etiqueta: "Entregado" },
  { valor: "cancelado", etiqueta: "Cancelado" },
]

// Clave de cada estado del API en el componente EtiquetaEstado.
export const ETIQUETA_ESTADO = {
  recibido: "recibido",
  en_preparacion: "preparacion",
  listo_despacho: "listo",
  en_camino: "camino",
  entregado: "entregado",
  cancelado: "cancelado",
}

const ACCION_ESTADO = {
  en_preparacion: "Iniciar preparación",
  listo_despacho: "Marcar como listo",
  en_camino: "Enviar a domicilio",
  entregado: "Marcar como entregado",
}

export function accionEstado(estado) {
  return ACCION_ESTADO[estado] ?? estado
}

export function textoTipoPedido(tipo) {
  return tipo === "domicilio" ? "Domicilio" : "Recoger en sede"
}

const ESTADOS_FINALES = ["entregado", "cancelado"]

// Devuelve los minutos que faltan y la hora estimada, o null si no aplica.
export function tiempoEstimado(pedido) {
  if (ESTADOS_FINALES.includes(pedido.estado)) return null
  if (!pedido.tiempo_estimado_entrega) return null

  const llegada = new Date(pedido.tiempo_estimado_entrega)
  const minutos = Math.round((llegada - Date.now()) / 60000)
  const hora = llegada.toLocaleTimeString("es-CO", { hour: "numeric", minute: "2-digit" })
  return { minutos, hora }
}

// Texto de la notificacion cuando cambia el estado de un pedido.
export function textoAviso(pedido) {
  const textos = {
    en_preparacion: "ya está en preparación",
    listo_despacho:
      pedido.tipo === "domicilio"
        ? "ya está listo y pronto saldrá a tu dirección"
        : "ya está listo para recoger en la sede",
    en_camino: "va en camino",
    entregado: "fue entregado. ¡Buen provecho!",
  }
  const texto = textos[pedido.estado]
  return texto ? `Tu pedido #${pedido.id} ${texto}` : null
}
