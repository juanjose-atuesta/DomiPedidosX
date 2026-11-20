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


CLAVE_PRUEBA = "ClaveSegura#2024"


def crear_usuario_prueba(email, rol, *, sede=None, telefono="3000000000", **extra):
    """Usuario con los campos obligatorios; el personal queda en `sede` si se indica."""
    from apps.sedes.models import SedeUsuario
    from apps.usuarios.models import PerfilRepartidor, User

    usuario = User.objects.create_user(
        negocio=negocio_de_rol(rol) if sede is None else (
            None if rol == Rol.CLIENTE else sede.negocio
        ),
        email=email,
        password=CLAVE_PRUEBA,
        nombre=extra.pop("nombre", email.split("@")[0].title()),
        apellido=extra.pop("apellido", "Prueba"),
        telefono=telefono,
        rol=rol,
        **extra,
    )
    if sede is not None and rol != Rol.CLIENTE:
        SedeUsuario.objects.create(usuario=usuario, sede=sede)
    if rol == Rol.REPARTIDOR:
        PerfilRepartidor.objects.create(usuario=usuario, disponible=True)
    return usuario


def producto_en_sede(sede, nombre="Hamburguesa", precio="15000", *, stock=None):
    """Producto del negocio de la sede, a la venta en ella. Sin `stock` no controla existencias."""
    from decimal import Decimal

    from apps.inventario.models import InventarioSede
    from apps.menu.models import Producto

    producto = Producto.objects.create(
        negocio=sede.negocio,
        nombre=nombre,
        precio_base=Decimal(precio),
        tiempo_preparacion_min=10,
    )
    InventarioSede.objects.create(
        sede=sede,
        producto=producto,
        controla_stock=stock is not None,
        stock_actual=stock or 0,
        stock_minimo=0,
    )
    return producto


def auth_prueba(usuario):
    """Cabecera Authorization con un access token del usuario."""
    from apps.usuarios.serializers import LoginSerializer

    token = LoginSerializer.get_token(usuario).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
