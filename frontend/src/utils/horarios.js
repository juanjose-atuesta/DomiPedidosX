export const DIAS_SEMANA = [
  { valor: "1", etiqueta: "Lunes", corto: "Lun" },
  { valor: "2", etiqueta: "Martes", corto: "Mar" },
  { valor: "3", etiqueta: "Miércoles", corto: "Mié" },
  { valor: "4", etiqueta: "Jueves", corto: "Jue" },
  { valor: "5", etiqueta: "Viernes", corto: "Vie" },
  { valor: "6", etiqueta: "Sábado", corto: "Sáb" },
  { valor: "7", etiqueta: "Domingo", corto: "Dom" },
]

export const OPCIONES_DIAS = DIAS_SEMANA.map(({ valor, etiqueta }) => ({
  valor,
  etiqueta,
}))

export function formatearHora(hora) {
  if (!hora) return ""

  const [horasTexto, minutosTexto] = String(hora).split(":")
  const horas = Number(horasTexto)
  const minutos = Number(minutosTexto)
  if (Number.isNaN(horas) || Number.isNaN(minutos)) return hora

  const sufijo = horas >= 12 ? "p.m." : "a.m."
  const hora12 = horas % 12 === 0 ? 12 : horas % 12
  return `${hora12}:${String(minutos).padStart(2, "0")} ${sufijo}`
}

export function normalizarHora(hora) {
  return String(hora ?? "").slice(0, 5)
}

export function resumenHorarios(horarios = []) {
  if (!horarios.length) return "Sin horario"

  const grupos = new Map()
  for (const horario of horarios) {
    const clave = `${horario.hora_apertura}|${horario.hora_cierre}`
    if (!grupos.has(clave)) {
      grupos.set(clave, {
        apertura: horario.hora_apertura,
        cierre: horario.hora_cierre,
        dias: [],
      })
    }
    grupos.get(clave).dias.push(Number(horario.dia_semana))
  }

  return [...grupos.values()]
    .map(({ apertura, cierre, dias }) => {
      const nombres = dias
        .sort((a, b) => a - b)
        .map((dia) => DIAS_SEMANA.find((d) => Number(d.valor) === dia)?.corto)
        .filter(Boolean)
        .join(", ")
      return `${nombres} ${formatearHora(apertura)} - ${formatearHora(cierre)}`
    })
    .join(" · ")
}
