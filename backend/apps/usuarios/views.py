from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsCocina, IsOperador, IsRepartidor
from .serializers import LoginSerializer

from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Direccion
from .serializers import DireccionSerializer, RolSerializer

User = get_user_model()

class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — inicio de sesión único para todos los roles."""

    serializer_class = LoginSerializer

# ---------------------------------------------------------------------------
# PROVISIONAL (HU login del personal, criterio 2)
# Estas tres vistas solo existen para comprobar que los permisos por rol
# funcionan mientras no existan los módulos reales. Cuando un módulo real esté
# listo: aplicarle el mismo permiso (IsOperador / IsCocina / IsRepartidor),
# borrar la vista provisional correspondiente y su ruta en urls.py.
# ---------------------------------------------------------------------------

class ModuloSedeView(APIView):
    """GET /api/auth/modulo-sede/ — solo operadores de sede (gestión de sede)."""

    permission_classes = [IsOperador]

    def get(self, request):
        return Response({"modulo": "gestion de sede"})


class ModuloCocinaView(APIView):
    """GET /api/auth/modulo-cocina/ — solo personal de cocina (tablero de cocina)."""

    permission_classes = [IsCocina]

    def get(self, request):
        return Response({"modulo": "tablero de cocina"})


class ModuloRepartidorView(APIView):
    """GET /api/auth/modulo-repartidor/ — solo repartidores (pedidos asignados)."""

    permission_classes = [IsRepartidor]

    def get(self, request):
        return Response({"modulo": "pedidos asignados"})

# HU 1.10: Desactivar cuenta de cliente
class DesactivarUsuarioView(APIView):
    permission_classes = [IsAdminUser] # Solo el admin de Django (is_staff=True) puede entrar

    def patch(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        usuario.is_active = False
        usuario.save()
        return Response({"mensaje": "Cuenta desactivada exitosamente"}, status=status.HTTP_200_OK)
    
