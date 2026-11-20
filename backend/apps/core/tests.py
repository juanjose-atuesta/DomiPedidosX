from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from apps.core.datos_prueba import negocio_de_rol
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .permissions import (
    EsAdmin,
    EsCliente,
    EsCocina,
    EsOperador,
    EsRepartidor,
)

PASSWORD = "ClaveSegura#2024"


class _VistaBase(APIView):
    def get(self, request):
        return Response({"ok": True})


class VistaCliente(_VistaBase):
    permission_classes = [EsCliente]


class VistaOperador(_VistaBase):
    permission_classes = [EsOperador]


class VistaCocina(_VistaBase):
    permission_classes = [EsCocina]


class VistaRepartidor(_VistaBase):
    permission_classes = [EsRepartidor]


class VistaAdmin(_VistaBase):
    permission_classes = [EsAdmin]


class VistaCocinaOperador(_VistaBase):
    permission_classes = [EsCocina | EsOperador]


urlpatterns = [
    path("test/cliente/", VistaCliente.as_view()),
    path("test/operador/", VistaOperador.as_view()),
    path("test/cocina/", VistaCocina.as_view()),
    path("test/repartidor/", VistaRepartidor.as_view()),
    path("test/admin/", VistaAdmin.as_view()),
    path("test/cocina-operador/", VistaCocinaOperador.as_view()),
]

VISTAS_POR_ROL = [
    (Rol.CLIENTE, "/test/cliente/"),
    (Rol.OPERADOR, "/test/operador/"),
    (Rol.COCINA, "/test/cocina/"),
    (Rol.REPARTIDOR, "/test/repartidor/"),
    (Rol.ADMIN, "/test/admin/"),
]


@override_settings(ROOT_URLCONF="apps.core.tests")
class PermisosPorRolTests(APITestCase):
    def _crear_usuario(self, rol, email=None, is_active=True):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol),
            email=email or f"{rol}@example.com",
            password=PASSWORD,
            nombre="Usuario",
            apellido="Prueba",
            telefono="3001234567",
            rol=rol,
            is_active=is_active,
        )

    def _token(self, usuario):
        refresh = LoginSerializer.get_token(usuario)
        return str(refresh.access_token)

    def _get(self, url, token=None):
        if token:
            return self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        return self.client.get(url)

    def test_matriz_de_acceso_por_rol(self):
        usuarios = {rol: self._crear_usuario(rol) for rol, _ in VISTAS_POR_ROL}

        for rol_vista, url in VISTAS_POR_ROL:
            for rol_visitante, usuario in usuarios.items():
                response = self._get(url, self._token(usuario))

                esperado = (
                    status.HTTP_200_OK
                    if rol_visitante == rol_vista
                    else status.HTTP_403_FORBIDDEN
                )
                self.assertEqual(
                    response.status_code,
                    esperado,
                    msg=f"rol={rol_visitante} url={url}",
                )

    def test_sin_token_da_401(self):
        for _, url in VISTAS_POR_ROL:
            response = self._get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_inactivo_con_token_emitido_no_accede(self):
        usuario = self._crear_usuario(Rol.CLIENTE)
        token = self._token(usuario)

        usuario.is_active = False
        usuario.save(update_fields=["is_active"])

        response = self._get("/test/cliente/", token)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permiso_rechaza_usuario_inactivo(self):
        usuario = self._crear_usuario(
            Rol.CLIENTE, email="inactivo@example.com", is_active=False
        )
        request = APIRequestFactory().get("/test/cliente/")
        request.user = usuario

        self.assertFalse(EsCliente().has_permission(request, None))

    def test_combinacion_de_roles_con_or(self):
        permitidos = [Rol.COCINA, Rol.OPERADOR]
        denegados = [Rol.CLIENTE, Rol.REPARTIDOR, Rol.ADMIN]

        for rol in permitidos:
            usuario = self._crear_usuario(rol, email=f"combo-{rol}@example.com")
            response = self._get("/test/cocina-operador/", self._token(usuario))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        for rol in denegados:
            usuario = self._crear_usuario(rol, email=f"combo-{rol}@example.com")
            response = self._get("/test/cocina-operador/", self._token(usuario))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cambio_de_rol_en_bd_aplica_aunque_el_token_siga_anterior(self):
        usuario = self._crear_usuario(Rol.CLIENTE, email="cambia@example.com")
        token = self._token(usuario)

        self.assertEqual(AccessToken(token)["rol"], Rol.CLIENTE)
        self.assertEqual(
            self._get("/test/cliente/", token).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self._get("/test/admin/", token).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        usuario.rol = Rol.ADMIN
        usuario.save(update_fields=["rol"])

        # El claim del token no cambió, pero el permiso consulta la base de datos.
        self.assertEqual(AccessToken(token)["rol"], Rol.CLIENTE)
        self.assertEqual(
            self._get("/test/admin/", token).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self._get("/test/cliente/", token).status_code,
            status.HTTP_403_FORBIDDEN,
        )
