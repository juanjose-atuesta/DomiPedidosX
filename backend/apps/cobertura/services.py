"""Reglas de cobertura: en qué zona de una sede cae un punto de entrega."""

import math
from decimal import Decimal
from datetime import datetime, time, timedelta
from .models import TipoCobertura, ZonaCobertura

from django.utils import timezone

RADIO_TIERRA_KM = 6371.0088
MINIMO_PUNTOS_POLIGONO = 3


def distancia_km(lat1, lng1, lat2, lng2):
    """Distancia en km entre dos coordenadas (fórmula del haversine)."""
    lat1, lng1, lat2, lng2 = (math.radians(float(v)) for v in (lat1, lng1, lat2, lng2))
    d_lat = lat2 - lat1
    d_lng = lng2 - lng1
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    )
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


def punto_en_poligono(lat, lng, poligono):
    """Ray casting sobre [[lat, lng], ...]. Los puntos del borde cuentan como dentro."""
    x, y = float(lng), float(lat)
    puntos = [(float(p[1]), float(p[0])) for p in poligono]
    dentro = False
    j = len(puntos) - 1
    for i, (xi, yi) in enumerate(puntos):
        xj, yj = puntos[j]
        # Sobre un lado: se considera cubierto.
        if (
            min(xi, xj) <= x <= max(xi, xj)
            and min(yi, yj) <= y <= max(yi, yj)
            and abs((xj - xi) * (y - yi) - (yj - yi) * (x - xi)) < 1e-12
        ):
            return True
        if (yi > y) != (yj > y):
            x_corte = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_corte:
                dentro = not dentro
        j = i
    return dentro


def zona_contiene(zona, lat, lng):
    if zona.tipo == TipoCobertura.RADIO:
        return distancia_km(zona.centro_lat, zona.centro_lng, lat, lng) <= float(
            zona.radio_km
        )
    return punto_en_poligono(lat, lng, zona.poligono or [])


def zonas_que_cubren(lat, lng, *, sedes=None):
    """Zonas activas (de sedes activas) que cubren el punto.

    Si varias cubren el mismo punto se prefiere la de menor tarifa.
    """
    zonas = ZonaCobertura.objects.filter(
        activa=True, sede__activa=True, sede__negocio__activo=True
    ).select_related("sede")
    if sedes is not None:
        zonas = zonas.filter(sede__in=sedes)
    cubren = [z for z in zonas if zona_contiene(z, lat, lng)]
    return sorted(cubren, key=lambda z: (z.tarifa_domicilio, z.nombre))


def zona_para_entrega(sede, lat, lng):
    """La zona de la sede que atiende el punto, o None si está fuera de cobertura."""
    zonas = zonas_que_cubren(lat, lng, sedes=[sede])
    return zonas[0] if zonas else None


def normalizar_poligono(poligono):
    """Valida y normaliza [[lat, lng], ...]. Lanza ValueError si no es válido."""
    if not isinstance(poligono, (list, tuple)):
        raise ValueError("El polígono debe ser una lista de puntos [lat, lng].")

    puntos = []
    for punto in poligono:
        if isinstance(punto, dict):
            punto = [punto.get("lat"), punto.get("lng")]
        if not isinstance(punto, (list, tuple)) or len(punto) != 2:
            raise ValueError("Cada punto del polígono debe ser [lat, lng].")
        try:
            lat, lng = float(punto[0]), float(punto[1])
        except (TypeError, ValueError):
            raise ValueError("Las coordenadas del polígono deben ser números.")
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError("Hay coordenadas del polígono fuera de rango.")
        puntos.append([lat, lng])

    # Un polígono cerrado (último = primero) no cuenta el punto repetido.
    if len(puntos) > 1 and puntos[0] == puntos[-1]:
        puntos.pop()
    if len({tuple(p) for p in puntos}) < MINIMO_PUNTOS_POLIGONO:
        raise ValueError(
            f"El polígono necesita al menos {MINIMO_PUNTOS_POLIGONO} puntos distintos."
        )
    return puntos


def validar_geometria(tipo, *, centro_lat, centro_lng, radio_km, poligono):
    """Devuelve los campos de geometría limpios según el tipo de zona."""
    if tipo == TipoCobertura.RADIO:
        if centro_lat is None or centro_lng is None:
            raise ValueError("Una zona por radio necesita el centro (latitud y longitud).")
        if radio_km is None or Decimal(str(radio_km)) <= 0:
            raise ValueError("El radio debe ser mayor que 0 km.")
        return {
            "centro_lat": centro_lat,
            "centro_lng": centro_lng,
            "radio_km": radio_km,
            "poligono": None,
        }
    if tipo == TipoCobertura.POLIGONO:
        return {
            "centro_lat": None,
            "centro_lng": None,
            "radio_km": None,
            "poligono": normalizar_poligono(poligono),
        }
    raise ValueError("El tipo de zona debe ser 'radio' o 'poligono'.")


def ocupacion_por_franja(sede, franjas, momento=None):
    """{franja.pk: pedidos en curso} de las franjas de la sede (HU-9.4).

    Cuenta los pedidos Recibidos o En preparación creados hoy dentro de cada
    franja, igual que `verificar_capacidad_sede` (HU-9.5). Las franjas de otro
    día de la semana quedan en None: hoy no tienen ocupación.
    """
    from apps.pedidos.capacidad import ESTADOS_EN_CURSO
    from apps.pedidos.models import Pedido

    franjas = list(franjas)
    if not franjas:
        return {}
    momento = timezone.localtime(momento)
    inicio_dia = timezone.make_aware(
        datetime.combine(momento.date(), time.min), timezone.get_current_timezone()
    )
    horas = [
        timezone.localtime(creado).time()
        for creado in Pedido.objects.filter(
            sede=sede,
            estado__in=ESTADOS_EN_CURSO,
            creado_en__gte=inicio_dia,
            creado_en__lt=inicio_dia + timedelta(days=1),
        ).values_list("creado_en", flat=True)
    ]
    hoy = momento.isoweekday()
    return {
        franja.pk: (
            sum(1 for hora in horas if franja.hora_inicio <= hora < franja.hora_fin)
            if franja.dia_semana == hoy
            else None
        )
        for franja in franjas
    }