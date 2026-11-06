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
