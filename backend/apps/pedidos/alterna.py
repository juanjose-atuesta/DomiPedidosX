"""Sede alterna cuando la sede del pedido está llena (HU-9.6).

Archivo nuevo: apps/pedidos/alterna.py
"""

from apps.cobertura.services import distancia_km, zonas_que_cubren
from apps.sedes.models import Sede

from .models import TipoPedido
from .services import cotizar_pedido


def sede_alterna_mas_cercana(
    sede,
    *,
    detalles,
    tipo,
    entrega_lat,
    entrega_lng,
    codigo_promocion="",
    promocion_id=None,
):
    """La sede del mismo negocio más cercana a la dirección de entrega que
    pueda atender hoy el pedido completo.

    Una sede es candidata si está activa, tiene una zona que cubre la
    dirección y vende todos los productos del carrito. Se recorren de la más
    cercana a la más lejana y gana la primera cuya cotización no tenga
    problemas (abierta, sin feriado, con capacidad disponible, pedido mínimo
    alcanzado). Un problema solo de la promoción no la descarta.

    Devuelve {"sede", "distancia_km", "cotizacion"} o None si ninguna puede
    (entonces no se muestra sede alterna). Solo aplica a domicilios.
    """
    if tipo != TipoPedido.DOMICILIO or entrega_lat is None or entrega_lng is None:
        return None

    candidatas = Sede.objects.filter(negocio_id=sede.negocio_id, activa=True).exclude(
        pk=sede.pk
    )
    cubiertas = {
        zona.sede_id: zona.sede
        for zona in zonas_que_cubren(entrega_lat, entrega_lng, sedes=candidatas)
    }

    def distancia(candidata):
        if candidata.latitud is None or candidata.longitud is None:
            return None
        return distancia_km(
            entrega_lat, entrega_lng, candidata.latitud, candidata.longitud
        )

    # Las que no tienen coordenadas van al final: no se sabe qué tan cerca están.
    ordenadas = sorted(
        ((distancia(c), c) for c in cubiertas.values()),
        key=lambda par: (par[0] is None, par[0] or 0, par[1].nombre),
    )

    for metros, candidata in ordenadas:
        try:
            cotizacion = cotizar_pedido(
                sede=candidata,
                detalles=detalles,
                tipo=tipo,
                entrega_lat=entrega_lat,
                entrega_lng=entrega_lng,
                codigo_promocion=codigo_promocion,
                promocion_id=promocion_id,
            )
        except ValueError:
            continue  # no vende algún producto del carrito
        problemas = [p for p in cotizacion["problemas"] if p != cotizacion["error_promocion"]]
        if not problemas:
            return {"sede": candidata, "distancia_km": metros, "cotizacion": cotizacion}
    return None