import { useState } from "react"

// Estado de las opciones elegidas de un producto ya normalizado.
export function useSeleccionOpciones(producto) {
  const [tamano, setTamano] = useState(0)
  const [adiciones, setAdiciones] = useState([])
  const [quitar, setQuitar] = useState([])

  const alternar = (lista, setLista, indice) =>
    setLista(lista.includes(indice) ? lista.filter((i) => i !== indice) : [...lista, indice])

  const opciones = [
    producto.tamanos[tamano],
    ...adiciones.map((i) => producto.adiciones[i]),
    ...quitar.map((i) => producto.excluibles[i]),
  ].filter(Boolean)

  return {
    producto,
    tamano,
    elegirTamano: setTamano,
    adiciones,
    alternarAdicion: (i) => alternar(adiciones, setAdiciones, i),
    quitar,
    alternarQuitar: (i) => alternar(quitar, setQuitar, i),
    opciones,
    extra: opciones.reduce((suma, o) => suma + o.extra, 0),
  }
}
