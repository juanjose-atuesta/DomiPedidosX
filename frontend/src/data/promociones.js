export const PROMOCIONES = [
  {
    id: 1, nombre: "Combo familiar", tipo: "Combo", descuento: 20,
    inicio: "2026-11-01", fin: "2026-11-30", cupo: 50, usados: 12,
    condiciones: "Pedido mínimo de $30.000", estado: "Activa",
    productos: ["Hamburguesa clásica", "Papas fritas"],
  },
  {
    id: 2, nombre: "2x1 en hamburguesas", tipo: "Descuento", descuento: 50,
    inicio: "2026-11-05", fin: "2026-11-15", cupo: 30, usados: 7,
    condiciones: "Aplica a la segunda hamburguesa", estado: "Activa",
    productos: ["Hamburguesa clásica"],
  },
  {
    id: 3, nombre: "Postre gratis", tipo: "Descuento", descuento: 100,
    inicio: "2026-10-01", fin: "2026-10-31", cupo: 20, usados: 20,
    condiciones: "Con pedidos desde $25.000", estado: "Vencida",
    productos: ["Brownie"],
  },
]

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

export function formatearFecha(aaaammdd) {
  const [, mes, dia] = aaaammdd.split("-")
  return `${Number(dia)} ${MESES[Number(mes) - 1]}`
}