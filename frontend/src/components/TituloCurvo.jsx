export default function TituloCurvo({ color = "#ffffff", className = "" }) {
  return (
    <svg viewBox="0 0 400 130" role="img" aria-label="DomiPedidosX" className={className}>
      <defs>
        <path id="arco-titulo" d="M 20 120 Q 200 -40 380 120" fill="none" />
      </defs>
      <text
        fill={color}
        fontSize="40"
        fontWeight="700"
        letterSpacing="-1"
        textAnchor="middle"
        className="font-titulo"
      >
        <textPath href="#arco-titulo" startOffset="50%">
          DomiPedidosX
        </textPath>
      </text>
    </svg>
  )
}