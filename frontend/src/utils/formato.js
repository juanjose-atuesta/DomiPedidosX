const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

// El API envía los precios como texto ("15000.00").
export function moneda(valor) {
  return `$${Number(valor).toLocaleString("es-CO")}`
}

export function formatearFecha(aaaammdd) {
  const [, mes, dia] = aaaammdd.split("-")
  return `${Number(dia)} ${MESES[Number(mes) - 1]}`
}

export function formatearHora(fechaIso) {
  return new Date(fechaIso).toLocaleTimeString("es-CO", {
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function fechaDeHoy() {
  const hoy = new Date()
  const mes = String(hoy.getMonth() + 1).padStart(2, "0")
  const dia = String(hoy.getDate()).padStart(2, "0")
  return `${hoy.getFullYear()}-${mes}-${dia}`
}
