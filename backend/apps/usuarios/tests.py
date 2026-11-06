import re
from uuid import uuid4

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


from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.sedes.models import Sede, SedeUsuario

from .models import PerfilRepartidor, Rol, User
from .serializers import LoginSerializer

PASSWORD = "ClaveSegura#2024"


class RegistroClienteTests(APITestCase):
    def setUp(self):
        self.url = reverse("registro_cliente")

    def _payload(self, **overrides):
        data = {
            "email": "nuevo@example.com",
            "nombre": "Ana",
            "apellido": "Gomez",
            "telefono": "3001234567",
            "password": PASSWORD,
            "password_confirmacion": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_registro_exitoso(self):
        response = self.client.post(
            self.url, self._payload(email="  Nuevo@Example.com  "), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

        usuario = User.objects.get(email="nuevo@example.com")
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_email_duplicado_sin_distinguir_mayusculas(self):
        User.objects.create_user(
            email="duplicado@example.com",
            password=PASSWORD,
            nombre="Otro",
            apellido="Cliente",
            telefono="3000000000",
        )

        response = self.client.post(
            self.url, self._payload(email="DUPLICADO@EXAMPLE.COM"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_contrasenas_no_coinciden(self):
        response = self.client.post(
            self.url,
            self._payload(password_confirmacion="OtraClave#2024"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_contrasena_debil(self):
        response = self.client.post(
            self.url,
            self._payload(password="12345678", password_confirmacion="12345678"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_campos_sensibles_ignorados(self):
        response = self.client.post(
            self.url,
            self._payload(
                rol=Rol.ADMIN,
                is_staff=True,
                is_active=False,
                is_superuser=True,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = User.objects.get(email="nuevo@example.com")
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertFalse(usuario.is_staff)
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_superuser)


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("login")
        self.usuario = User.objects.create_user(
            email="cliente@example.com",
            password=PASSWORD,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
        )

    def test_login_exitoso(self):
        response = self.client.post(
            self.url,
            {"email": "cliente@example.com", "password": PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        token = AccessToken(response.data["access"])
        self.assertEqual(token["rol"], Rol.CLIENTE)

    def test_login_contrasena_incorrecta(self):
        response = self.client.post(
            self.url,
            {"email": "cliente@example.com", "password": "Incorrecta#2024"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_inexistente_mismo_mensaje(self):
        respuesta_inexistente = self.client.post(
            self.url,
            {"email": "nadie@example.com", "password": PASSWORD},
            format="json",
        )
        respuesta_incorrecta = self.client.post(
            self.url,
            {"email": "cliente@example.com", "password": "Incorrecta#2024"},
            format="json",
        )

        self.assertEqual(
            respuesta_inexistente.status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(
            respuesta_inexistente.data["detail"],
            respuesta_incorrecta.data["detail"],
        )

    def test_login_usuario_inactivo(self):
        self.usuario.is_active = False
        self.usuario.save(update_fields=["is_active"])

        response = self.client.post(
            self.url,
            {"email": "cliente@example.com", "password": PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_con_mayusculas(self):
        response = self.client.post(
            self.url,
            {"email": "CLIENTE@EXAMPLE.COM", "password": PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class RefreshTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_refresh")
        User.objects.create_user(
            email="cliente@example.com",
            password=PASSWORD,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
        )

    def _obtener_refresh(self):
        response = self.client.post(
            reverse("login"),
            {"email": "cliente@example.com", "password": PASSWORD},
            format="json",
        )
        return response.data["refresh"]

    def test_refresh_exitoso(self):
        refresh = self._obtener_refresh()

        response = self.client.post(self.url, {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_token_invalido(self):
        response = self.client.post(
            self.url, {"refresh": "token-invalido"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuario_me")
        self.usuario = User.objects.create_user(
            email="cliente@example.com",
            password=PASSWORD,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
        )

    def _obtener_access(self):
        response = self.client.post(
            reverse("login"),
            {"email": "cliente@example.com", "password": PASSWORD},
            format="json",
        )
        return response.data["access"]

    def test_me_sin_token(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_con_token_valido(self):
        access = self._obtener_access()

        response = self.client.get(
            self.url, HTTP_AUTHORIZATION=f"Bearer {access}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.usuario.id))
        self.assertEqual(response.data["nombre"], self.usuario.nombre)
        self.assertEqual(response.data["apellido"], self.usuario.apellido)
        self.assertEqual(response.data["email"], self.usuario.email)
        self.assertEqual(response.data["telefono"], self.usuario.telefono)
        self.assertEqual(response.data["rol"], self.usuario.rol)

    def test_me_con_token_alterado(self):
        access = self._obtener_access()
        alterado = access[:-1] + ("a" if access[-1] != "a" else "b")

        response = self.client.get(
            self.url, HTTP_AUTHORIZATION=f"Bearer {alterado}"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistroPersonalTests(APITestCase):
    def setUp(self):
        self.url = reverse("registro_personal")
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            nombre="Admin",
            apellido="Principal",
            telefono="3001111111",
            rol=Rol.ADMIN,
            is_staff=True,
        )
        self.sede1 = Sede.objects.create(
            nombre="Sede Norte", direccion="Calle 1"
        )
        self.sede2 = Sede.objects.create(
            nombre="Sede Sur", direccion="Calle 2"
        )
        self.sede_inactiva = Sede.objects.create(
            nombre="Sede Cerrada", direccion="Calle 3", activa=False
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _payload(self, **overrides):
        data = {
            "email": "personal@example.com",
            "nombre": "Nuevo",
            "apellido": "Personal",
            "telefono": "3001234567",
            "rol": Rol.OPERADOR,
            "sedes_ids": [str(self.sede1.id)],
            "password": PASSWORD,
            "password_confirmacion": PASSWORD,
        }
        data.update(overrides)
        return data

    def _post(self, payload, token=None):
        if token:
            return self.client.post(
                self.url,
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
        return self.client.post(self.url, payload, format="json")

    def test_admin_crea_personal_operativo_con_sedes(self):
        token = self._token(self.admin)
        casos = [
            (Rol.OPERADOR, "operador@example.com"),
            (Rol.COCINA, "cocina@example.com"),
            (Rol.REPARTIDOR, "repartidor@example.com"),
        ]

        for rol, email in casos:
            response = self._post(
                self._payload(
                    email=email,
                    rol=rol,
                    sedes_ids=[str(self.sede1.id), str(self.sede2.id)],
                ),
                token,
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["usuario"]["rol"], rol)
            self.assertEqual(len(response.data["usuario"]["sedes"]), 2)

            usuario = User.objects.get(email=email)
            self.assertEqual(usuario.rol, rol)
            self.assertEqual(
                SedeUsuario.objects.filter(usuario=usuario).count(), 2
            )

    def test_repartidor_crea_su_perfil_automaticamente(self):
        response = self._post(
            self._payload(
                rol=Rol.REPARTIDOR, email="repartidor.perfil@example.com"
            ),
            self._token(self.admin),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        usuario = User.objects.get(email="repartidor.perfil@example.com")
        perfil = PerfilRepartidor.objects.get(usuario=usuario)
        self.assertFalse(perfil.disponible)

    def test_admin_crea_otro_admin_sin_sedes(self):
        response = self._post(
            self._payload(
                rol=Rol.ADMIN, email="admin2@example.com", sedes_ids=[]
            ),
            self._token(self.admin),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"]["rol"], Rol.ADMIN)
        self.assertEqual(response.data["usuario"]["sedes"], [])

        usuario = User.objects.get(email="admin2@example.com")
        self.assertTrue(usuario.is_staff)
        self.assertFalse(
            PerfilRepartidor.objects.filter(usuario=usuario).exists()
        )

    def test_personal_operativo_sin_sedes_da_400(self):
        token = self._token(self.admin)

        response_vacio = self._post(self._payload(sedes_ids=[]), token)
        self.assertEqual(
            response_vacio.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("sedes_ids", response_vacio.data)

        payload_sin_campo = self._payload(email="sin.sede@example.com")
        payload_sin_campo.pop("sedes_ids")
        response_sin_campo = self._post(payload_sin_campo, token)
        self.assertEqual(
            response_sin_campo.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("sedes_ids", response_sin_campo.data)

    def test_sede_inexistente_o_inactiva_da_400(self):
        token = self._token(self.admin)

        response_inexistente = self._post(
            self._payload(sedes_ids=[str(uuid4())]), token
        )
        self.assertEqual(
            response_inexistente.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("sedes_ids", response_inexistente.data)

        response_inactiva = self._post(
            self._payload(
                email="sede.inactiva@example.com",
                sedes_ids=[str(self.sede_inactiva.id)],
            ),
            token,
        )
        self.assertEqual(
            response_inactiva.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("sedes_ids", response_inactiva.data)

    def test_cliente_no_puede_usar_el_endpoint(self):
        cliente = User.objects.create_user(
            email="cliente.endpoint@example.com",
            password=PASSWORD,
            nombre="Cliente",
            apellido="Prueba",
            telefono="3002222222",
        )

        response = self._post(self._payload(), self._token(cliente))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_token_da_401(self):
        response = self._post(self._payload())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_permite_crear_clientes(self):
        response = self._post(
            self._payload(rol=Rol.CLIENTE), self._token(self.admin)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rol", response.data)

    def test_email_duplicado_sin_distinguir_mayusculas(self):
        User.objects.create_user(
            email="personal.dup@example.com",
            password=PASSWORD,
            nombre="Existente",
            apellido="Prueba",
            telefono="3003333333",
            rol=Rol.COCINA,
        )

        response = self._post(
            self._payload(email="PERSONAL.DUP@EXAMPLE.COM"),
            self._token(self.admin),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.solicitar_url = reverse("solicitar_password_reset")
        self.confirmar_url = reverse("confirmar_password_reset")
        self.usuario = User.objects.create_user(
            email="cliente@example.com",
            password=PASSWORD,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
        )
        mail.outbox.clear()

    def _solicitar(self, email="cliente@example.com"):
        return self.client.post(
            self.solicitar_url, {"email": email}, format="json"
        )

    def _extraer_credenciales(self, cuerpo):
        uidb64 = re.search(r"uid: (\S+)", cuerpo).group(1)
        token = re.search(r"token: (\S+)", cuerpo).group(1)
        return uidb64, token

    def _confirmar(self, uidb64, token, new_password):
        return self.client.post(
            self.confirmar_url,
            {
                "uidb64": uidb64,
                "token": token,
                "new_password": new_password,
            },
            format="json",
        )

    def test_solicitud_con_correo_existente_envia_email(self):
        response = self._solicitar("CLIENTE@EXAMPLE.COM")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["cliente@example.com"])
        self.assertIn("uid:", mail.outbox[0].body)
        self.assertIn("token:", mail.outbox[0].body)

    def test_solicitud_con_correo_inexistente_no_revela_ni_envia(self):
        respuesta_existente = self._solicitar()
        respuesta_inexistente = self._solicitar("nadie@example.com")

        self.assertEqual(
            respuesta_existente.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            respuesta_inexistente.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            respuesta_existente.data["mensaje"],
            respuesta_inexistente.data["mensaje"],
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_confirmacion_exitosa_cambia_la_contrasena(self):
        self._solicitar()
        uidb64, token = self._extraer_credenciales(mail.outbox[0].body)
        nueva_password = "NuevaClave#2026"

        response = self._confirmar(uidb64, token, nueva_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(nueva_password))
        self.assertFalse(self.usuario.check_password(PASSWORD))

    def test_confirmacion_con_token_alterado_da_400(self):
        self._solicitar()
        uidb64, token = self._extraer_credenciales(mail.outbox[0].body)
        alterado = token[:-1] + ("a" if token[-1] != "a" else "b")

        response = self._confirmar(uidb64, alterado, "NuevaClave#2026")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(PASSWORD))

    @override_settings(PASSWORD_RESET_TIMEOUT=-1)
    def test_confirmacion_con_token_expirado_da_400(self):
        self._solicitar()
        uidb64, token = self._extraer_credenciales(mail.outbox[0].body)

        response = self._confirmar(uidb64, token, "NuevaClave#2026")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirmacion_con_contrasena_debil_da_400(self):
        self._solicitar()
        uidb64, token = self._extraer_credenciales(mail.outbox[0].body)

        response = self._confirmar(uidb64, token, "12345678")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(PASSWORD))

    def test_confirmacion_con_uid_invalido_da_400(self):
        response = self._confirmar(
            "uid-invalido", "token-invalido", "NuevaClave#2026"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActualizarPerfilTests(APITestCase):
    def setUp(self):
        self.url = reverse("usuario_me")
        self.usuario = User.objects.create_user(
            email="cliente@example.com",
            password=PASSWORD,
            nombre="Juan",
            apellido="Perez",
            telefono="3001234567",
        )
        self.token = str(
            LoginSerializer.get_token(self.usuario).access_token
        )

    def _patch(self, payload, token=None):
        if token:
            return self.client.patch(
                self.url,
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
        return self.client.patch(self.url, payload, format="json")

    def test_patch_actualiza_nombre_apellido_y_telefono(self):
        response = self._patch(
            {
                "nombre": "Ana",
                "apellido": "Gomez",
                "telefono": "3119999999",
            },
            self.token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre, "Ana")
        self.assertEqual(self.usuario.apellido, "Gomez")
        self.assertEqual(self.usuario.telefono, "3119999999")
        self.assertEqual(response.data["nombre"], "Ana")

    def test_patch_parcial_solo_actualiza_el_campo_enviado(self):
        response = self._patch(
            {"telefono": "3228888888"}, self.token
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.telefono, "3228888888")
        self.assertEqual(self.usuario.nombre, "Juan")
        self.assertEqual(self.usuario.apellido, "Perez")

    def test_patch_ignora_email_rol_e_is_staff(self):
        email_original = self.usuario.email

        response = self._patch(
            {
                "nombre": "Nuevo",
                "email": "otro@example.com",
                "rol": Rol.ADMIN,
                "is_staff": True,
            },
            self.token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre, "Nuevo")
        self.assertEqual(self.usuario.email, email_original)
        self.assertEqual(self.usuario.rol, Rol.CLIENTE)
        self.assertFalse(self.usuario.is_staff)

    def test_patch_sin_token_da_401(self):
        response = self._patch({"telefono": "3000000000"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
