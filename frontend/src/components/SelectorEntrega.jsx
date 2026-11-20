import CampoSelect from "./CampoSelect"

const TIPOS = [
  { valor: "domicilio", etiqueta: "Domicilio" },
  { valor: "recoger", etiqueta: "Recoger en sede" },
]

export default function SelectorEntrega({
  tipo,
  onCambiarTipo,
  direcciones,
  direccionId,
  onCambiarDireccion,
  sinDirecciones,
}) {
  return (
    <div className="flex flex-col gap-3">
      <CampoSelect
        etiqueta="Tipo de entrega"
        opciones={TIPOS}
        value={tipo}
        onChange={(e) => onCambiarTipo(e.target.value)}
      />
      {tipo === "domicilio" &&
        (direcciones.length > 0 ? (
          <CampoSelect
            etiqueta="Dirección de entrega"
            opciones={direcciones.map((d) => ({
              valor: d.id,
              etiqueta: `${d.alias}: ${d.direccion_texto}`,
            }))}
            value={direccionId}
            onChange={(e) => onCambiarDireccion(e.target.value)}
          />
        ) : (
          sinDirecciones
        ))}
    </div>
  )
}
