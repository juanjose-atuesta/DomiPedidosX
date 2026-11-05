export const COBERTURA = { centro: [3.4516, -76.532], radioKm: 8 }

const RADIO_TIERRA_KM = 6371
const aRadianes = (grados) => (grados * Math.PI) / 180

export function distanciaKm([lat1, lng1], [lat2, lng2]) {
  const dLat = aRadianes(lat2 - lat1)
  const dLng = aRadianes(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(aRadianes(lat1)) * Math.cos(aRadianes(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * RADIO_TIERRA_KM * Math.asin(Math.sqrt(a))
}

export function estaEnCobertura(posicion) {
  return distanciaKm(posicion, COBERTURA.centro) <= COBERTURA.radioKm
}