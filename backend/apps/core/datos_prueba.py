"""Datos compartidos por las pruebas."""

from apps.negocios.models import Negocio
from apps.usuarios.models import Rol


def negocio_prueba():
    return Negocio.objects.get_or_create(nombre="Negocio de prueba")[0]


def negocio_de_rol(rol):
    """El personal pertenece a un negocio; los clientes no."""
    return None if rol == Rol.CLIENTE else negocio_prueba()


# Punto de entrega por defecto de las pruebas (centro de Cali).
LAT_PRUEBA = "3.45"
LNG_PRUEBA = "-76.53"


def habilitar_sede_para_pedidos(
    sede, *, tarifa="0", pedido_minimo="0", radio_km="50", tiempo_min=30
):
    """Deja la sede abierta todo el día y con una zona que cubre el punto de prueba.

    Crear pedidos exige horario abierto y, a domicilio, una zona de cobertura.
    """
    from datetime import time
    from decimal import Decimal

    from apps.cobertura.models import TipoCobertura, ZonaCobertura
    from apps.sedes.models import HorarioAtencion

    HorarioAtencion.objects.bulk_create(
        [
            HorarioAtencion(
                sede=sede,
                dia_semana=dia,
                hora_apertura=time(0, 0),
                hora_cierre=time(23, 59, 59, 999999),
            )
            for dia in range(1, 8)
        ]
    )
    return ZonaCobertura.objects.create(
        sede=sede,
        nombre="Zona de prueba",
        tipo=TipoCobertura.RADIO,
        centro_lat=Decimal(LAT_PRUEBA),
        centro_lng=Decimal(LNG_PRUEBA),
        radio_km=Decimal(radio_km),
        tarifa_domicilio=Decimal(tarifa),
        pedido_minimo=Decimal(pedido_minimo),
        tiempo_estimado_min=tiempo_min,
    )
