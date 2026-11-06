"""Datos compartidos por las pruebas."""

from apps.negocios.models import Negocio
from apps.usuarios.models import Rol


def negocio_prueba():
    return Negocio.objects.get_or_create(nombre="Negocio de prueba")[0]


def negocio_de_rol(rol):
    """El personal pertenece a un negocio; los clientes no."""
    return None if rol == Rol.CLIENTE else negocio_prueba()
