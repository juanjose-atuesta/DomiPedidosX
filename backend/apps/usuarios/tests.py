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

# --- Criterio 2: cada rol accede solo a su módulo ---------------------------

# Qué módulo (nombre de URL) le corresponde a cada rol del personal
MODULO_DE = {
    Rol.OPERADOR: "modulo-sede",
    Rol.COCINA: "modulo-cocina",
    Rol.REPARTIDOR: "modulo-repartidor",
}


def get_con_token(rol, url_name):
    """Inicia sesión como un usuario del rol dado y consulta el módulo con su token.

    Reproduce lo que hará el frontend: login -> guardar `access` -> enviarlo en
    la cabecera Authorization en cada petición.
    """
    email = f"{rol}@x.com"
    # Evita crear dos veces el mismo correo dentro de una misma prueba (es único)
    if not User.objects.filter(email=email).exists():
        crear_usuario(email, rol)
    access = post_login(email, CLAVE).data["access"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client.get(reverse(url_name))


@pytest.mark.django_db
@pytest.mark.parametrize("rol", list(MODULO_DE))
def test_cada_rol_accede_a_su_modulo(rol):
    """Criterio 2: el usuario entra al módulo de su rol (200)."""
    assert get_con_token(rol, MODULO_DE[rol]).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("rol", list(MODULO_DE))
def test_rol_no_accede_a_modulos_ajenos(rol):
    """Criterio 2: el usuario recibe 403 en los módulos de los otros roles."""
    for otro, url_name in MODULO_DE.items():
        if otro != rol:
            # El mensaje extra indica qué combinación falló si la prueba se rompe
            assert get_con_token(rol, url_name).status_code == 403, (rol, url_name)


@pytest.mark.django_db
def test_cliente_no_accede_a_modulos_del_personal():
    """Un cliente autenticado no puede entrar a ningún módulo del personal (403)."""
    for url_name in MODULO_DE.values():
        assert get_con_token(Rol.CLIENTE, url_name).status_code == 403


@pytest.mark.django_db
def test_sin_token_no_accede():
    """Sin sesión iniciada el módulo responde 401 (no autenticado)."""
    assert APIClient().get(reverse("modulo-cocina")).status_code == 401