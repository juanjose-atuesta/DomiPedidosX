from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.core.permissions import EsAdmin
from .models import Direccion
from .serializers import (
    RegistroClienteSerializer,
    LoginSerializer,
    UsuarioSerializer,
    RegistroPersonalSerializer,
    PersonalSerializer,
    SolicitarPasswordResetSerializer,
    ConfirmarPasswordResetSerializer,
    ActualizarPerfilSerializer,
    DireccionSerializer,
    RolSerializer,
)
from .services import (
    registrar_cliente,
    crear_usuario_personal,
    solicitar_recuperacion_password,
    confirmar_recuperacion_password,
    actualizar_perfil_usuario,
)

User = get_user_model()

# ==========================================
# VISTAS DE DEVELOP (Login, Registro, etc.)
# ==========================================

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
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ActualizarPerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usuario = actualizar_perfil_usuario(request.user, **serializer.validated_data)
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_200_OK)

class RegistroPersonalView(APIView):
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
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConfirmarPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            confirmar_recuperacion_password(**serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"mensaje": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )

# ==========================================
# TUS VISTAS (HU 1.6, 1.9 y 1.10)
# ==========================================

class DesactivarUsuarioView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        usuario.is_active = False
        usuario.save()
        return Response({"mensaje": "Cuenta desactivada exitosamente"}, status=status.HTTP_200_OK)

class CambiarRolView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        serializer = RolSerializer(data=request.data)
        if serializer.is_valid():
            usuario.rol = serializer.validated_data['rol']
            usuario.save()
            return Response({"mensaje": f"Rol actualizado a {usuario.rol}"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DireccionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        direcciones = Direccion.objects.filter(cliente=request.user, activa=True)
        serializer = DireccionSerializer(direcciones, many=True)
        return Response(serializer.data)

    def post(self, request):
        if Direccion.objects.filter(cliente=request.user, activa=True).count() >= 5:
            return Response({"error": "Máximo 5 direcciones permitidas"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DireccionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cliente=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    