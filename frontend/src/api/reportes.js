import api from "./cliente"

// Reporte de ventas por sede y zona en un período (fechas AAAA-MM-DD, ambas incluidas).
export async function obtenerVentasSedeZona(desde, hasta) {
  const { data } = await api.get("/reportes/ventas-sede-zona/", { params: { desde, hasta } })
  return data
}