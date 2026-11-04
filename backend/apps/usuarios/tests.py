from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Rol, User

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
