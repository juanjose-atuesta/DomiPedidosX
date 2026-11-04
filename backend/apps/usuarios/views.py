from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .serializers import (
    RegistroClienteSerializer,
    LoginSerializer,
    UsuarioSerializer,
)
from .services import registrar_cliente


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
    401. Si es válido, devuelve id, nombre, apellido, email, teléfono y rol.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
