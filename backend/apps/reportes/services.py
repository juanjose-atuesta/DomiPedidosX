from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from apps.cobertura.models import ZonaCobertura
from apps.pedidos.models import EstadoPedido, Pedido
from apps.sedes.models import Sede

CERO = Decimal("0.00")


def _limites_del_periodo(desde, hasta):
    """Convierte las fechas (ambas incluidas) en un rango [inicio, fin) de la zona horaria local."""
    zona_horaria = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(desde, time.min), zona_horaria)
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min), zona_horaria)
    return inicio, fin


def ventas_por_sede_y_zona(negocio, desde, hasta):
    """Pedidos y valor vendido de cada sede y cada zona del negocio en el período (HU-10.5).

    Excluye los pedidos cancelados. Lista todas las sedes y zonas del negocio,
    incluso las que no vendieron nada, y agrupa aparte los pedidos sin zona
    (por ejemplo, los de recogida en la sede).
    """
    inicio, fin = _limites_del_periodo(desde, hasta)
    filas = (
        Pedido.objects.filter(sede__negocio=negocio, creado_en__gte=inicio, creado_en__lt=fin)
        .exclude(estado=EstadoPedido.CANCELADO)
        .values("sede_id", "zona_id")
        .annotate(numero_pedidos=Count("id"), valor_vendido=Sum("total"))
    )
    ventas = {(f["sede_id"], f["zona_id"]): f for f in filas}

    def dato(sede_id, zona_id):
        fila = ventas.get((sede_id, zona_id))
        return {
            "numero_pedidos": fila["numero_pedidos"] if fila else 0,
            "valor_vendido": fila["valor_vendido"] if fila else CERO,
        }

    zonas_por_sede = {}
    for zona in ZonaCobertura.objects.filter(sede__negocio=negocio).order_by("nombre"):
        zonas_por_sede.setdefault(zona.sede_id, []).append(zona)

    sedes = []
    for sede in Sede.objects.filter(negocio=negocio).order_by("nombre"):
        zonas = [
            {"zona_id": str(z.id), "zona_nombre": z.nombre, **dato(sede.id, z.id)}
            for z in zonas_por_sede.get(sede.id, [])
        ]
        sin_zona = dato(sede.id, None)
        if sin_zona["numero_pedidos"]:
            zonas.append({"zona_id": None, "zona_nombre": "Sin zona", **sin_zona})
        sedes.append(
            {
                "sede_id": str(sede.id),
                "sede_nombre": sede.nombre,
                "numero_pedidos": sum(z["numero_pedidos"] for z in zonas),
                "valor_vendido": sum((z["valor_vendido"] for z in zonas), CERO),
                "zonas": zonas,
            }
        )

    return {
        "desde": desde,
        "hasta": hasta,
        "total_pedidos": sum(s["numero_pedidos"] for s in sedes),
        "total_vendido": sum((s["valor_vendido"] for s in sedes), CERO),
        "sedes": sedes,
    }