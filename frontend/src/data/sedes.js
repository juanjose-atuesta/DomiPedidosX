export const SEDES = [
  { id: 1, nombre: "Sede Centro", direccion: "Cra 5 #10-20", telefono: "602 555 0101", ciudad: "Cali", apertura: "11:00", cierre: "22:00", activa: true },
  { id: 2, nombre: "Sede Norte", direccion: "Calle 40 #3N-15", telefono: "602 555 0102", ciudad: "Cali", apertura: "11:00", cierre: "21:00", activa: true },
  { id: 3, nombre: "Sede Sur", direccion: "Av. 6 #45-10", telefono: "602 555 0103", ciudad: "Cali", apertura: "12:00", cierre: "21:00", activa: false },
]

export function formatearHora(hhmm) {
  const [h, m] = hhmm.split(":").map(Number)
  const sufijo = h >= 12 ? "p.m." : "a.m."
  const h12 = h % 12 === 0 ? 12 : h % 12
  return `${h12}:${String(m).padStart(2, "0")} ${sufijo}`
}