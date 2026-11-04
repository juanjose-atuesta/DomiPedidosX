from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from apps.core.permissions import EsAdmin

from .serializers import (
    RegistroClienteSerializer,
    LoginSerializer,
    UsuarioSerializer,
    RegistroPersonalSerializer,
    PersonalSerializer,
    SolicitarPasswordResetSerializer,
    ConfirmarPasswordResetSerializer,
    ActualizarPerfilSerializer,
)
from .services import (
    registrar_cliente,
    crear_usuario_personal,
    solicitar_recuperacion_password,
    confirmar_recuperacion_password,
    actualizar_perfil_usuario,
)


class RegistroClienteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data
        usuario = registrar_cliente(**datos)

        return Response(
            {
                "mensaje": "Usuario registrado exitosamente",
                "id": str(usuario.id),
                "email": usuario.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Endpoint de login.

    Recibe email y contraseña, delega la validación a LoginSerializer y
    responde 200 con {"access", "refresh"} o 401 con un mensaje genérico si
    las credenciales no son válidas o el usuario está inactivo.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class MeView(APIView):
    """Datos del usuario autenticado.

    JWTAuthentication valida el Bearer token; si falta o es inválido responde
    401. GET devuelve id, nombre, apellido, email, teléfono y rol. PATCH
    permite actualizar únicamente nombre, apellido y teléfono.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ActualizarPerfilSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        usuario = actualizar_perfil_usuario(
            request.user, **serializer.validated_data
        )
        return Response(
            UsuarioSerializer(usuario).data, status=status.HTTP_200_OK
        )


class RegistroPersonalView(APIView):
    """Registro de personal del restaurante por parte de un administrador.

    Solo un usuario con rol admin puede crear operadores, cocineros,
    repartidores o administradores adicionales, asignándoles sus sedes.
    """

    permission_classes = [EsAdmin]

    def post(self, request):
        serializer = RegistroPersonalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data
        sedes_ids = datos.pop("sedes_ids", [])
        usuario = crear_usuario_personal(**datos, sedes_ids=sedes_ids)

        return Response(
            {
                "mensaje": "Usuario de personal registrado exitosamente",
                "usuario": PersonalSerializer(usuario).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SolicitarPasswordResetView(APIView):
    """Solicita el envío del correo de recuperación de contraseña.

    Responde siempre el mismo mensaje, exista o no el correo, para no revelar
    qué usuarios están registrados.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SolicitarPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitar_recuperacion_password(**serializer.validated_data)

        return Response(
            {
                "mensaje": (
                    "Si el correo está registrado, recibirás instrucciones "
                    "para restablecer tu contraseña."
                )
            },
            status=status.HTTP_200_OK,
        )


class ConfirmarPasswordResetView(APIView):
    """Confirma el restablecimiento usando uidb64, token y nueva contraseña."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConfirmarPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            confirmar_recuperacion_password(**serializer.validated_data)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        except DjangoValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"mensaje": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )
