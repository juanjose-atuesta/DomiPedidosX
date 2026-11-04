const ESTADOS = {
  recibido: { texto: "Recibido", clases: "bg-texto-sec text-white" },
  preparacion: { texto: "En preparación", clases: "bg-ambar text-texto" },
  listo: { texto: "Listo para despacho", clases: "bg-amarillo text-texto" },
  camino: { texto: "En camino", clases: "bg-info text-white" },
  entregado: { texto: "Entregado", clases: "bg-exito text-white" },
  cancelado: { texto: "Cancelado", clases: "bg-primario text-white" },
}

export default function EtiquetaEstado({ estado = "recibido", children }) {
  const { texto, clases } = ESTADOS[estado]
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${clases}`}
    >
      {children ?? texto}
    </span>
  )
}