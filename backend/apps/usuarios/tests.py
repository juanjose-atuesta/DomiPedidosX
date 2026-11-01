from django.test import TestCase

"""Pruebas del login con JWT (criterios de aceptación de la HU)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.usuarios.models import Rol, User

CLAVE = "Clave123!"


def crear_usuario(email, rol, **extra):
    """Crea un usuario con los campos obligatorios del modelo."""
    return User.objects.create_user(
        email=email, password=CLAVE, rol=rol,
        nombre="Prueba", apellido="Uno", telefono="3000000000", **extra,
    )


def post_login(email, password):
    return APIClient().post(reverse("login"), {"email": email, "password": password})


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Rol.OPERADOR, Rol.COCINA, Rol.REPARTIDOR])
def test_token_incluye_rol_y_expira_en_60_min(rol):
    """Criterio 1: con credenciales correctas, el JWT trae el rol y dura 60 minutos."""
    crear_usuario("personal@x.com", rol)

    r = post_login("personal@x.com", CLAVE)

    assert r.status_code == 200
    token = AccessToken(r.data["access"])
    assert token["rol"] == rol
    assert token["exp"] - token["iat"] == 3600
    assert r.data["user"]["rol"] == rol


@pytest.mark.django_db
def test_cuenta_desactivada():
    """Criterio 3: una cuenta desactivada no inicia sesión y ve 'Cuenta desactivada'."""
    crear_usuario("off@x.com", Rol.COCINA, is_active=False)

    r = post_login("off@x.com", CLAVE)

    assert r.status_code == 401
    assert r.data["detail"] == "Cuenta desactivada"
    assert "access" not in r.data


@pytest.mark.django_db
def test_mensaje_generico_en_credenciales_incorrectas():
    """Criterio 4: correo inexistente y clave mala dan exactamente el mismo mensaje."""
    crear_usuario("chef@x.com", Rol.COCINA)

    clave_mala = post_login("chef@x.com", "mala")
    correo_malo = post_login("nadie@x.com", CLAVE)

    assert clave_mala.status_code == correo_malo.status_code == 401
    assert clave_mala.data["detail"] == correo_malo.data["detail"] == "Credenciales incorrectas"


@pytest.mark.django_db
def test_cuenta_desactivada_con_clave_mala_no_revela_estado():
    """Una cuenta desactivada con clave incorrecta ve el mensaje genérico, no 'desactivada'."""
    crear_usuario("off@x.com", Rol.COCINA, is_active=False)

    r = post_login("off@x.com", "mala")

    assert r.data["detail"] == "Credenciales incorrectas"