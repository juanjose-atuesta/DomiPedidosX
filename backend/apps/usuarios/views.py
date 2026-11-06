from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import EsAdmin, EsCocina, EsOperador, EsRepartidor
from .models import Direccion, Rol
from .serializers import (
    RegistroClienteSerializer,
    LoginSerializer,
    UsuarioSerializer,
    RegistroPersonalSerializer,
    PersonalSerializer,
    SolicitarPasswordResetSerializer,
    ConfirmarPasswordResetSerializer,
    ActualizarPerfilSerializer,
    ClienteBusquedaSerializer,
    DireccionSerializer,
    RolSerializer,
)
from .services import (
    registrar_cliente,
    crear_usuario_personal,
    solicitar_recuperacion_password,
    confirmar_recuperacion_password,
    actualizar_perfil_usuario,
    desactivar_direccion,
    guardar_direccion,
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
    permission_classes = [EsAdmin]

    def patch(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        usuario.is_active = False
        usuario.save()
        return Response({"mensaje": "Cuenta desactivada exitosamente"}, status=status.HTTP_200_OK)

class UsuarioListAdminView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        usuarios = (
            User.objects.filter(is_active=True)
            .prefetch_related("sedes_asignadas__sede")
            .order_by("nombre", "apellido")
        )
        serializer = PersonalSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CambiarRolView(APIView):
    permission_classes = [EsAdmin]

    def patch(self, request, pk):
        usuario = get_object_or_404(User, pk=pk)
        serializer = RolSerializer(data=request.data)
        if serializer.is_valid():
            usuario.rol = serializer.validated_data['rol']
            usuario.is_staff = usuario.rol == Rol.ADMIN
            usuario.save(update_fields=["rol", "is_staff"])
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
        serializer.is_valid(raise_exception=True)
        direccion = guardar_direccion(request.user, **serializer.validated_data)
        return Response(
            DireccionSerializer(direccion).data, status=status.HTTP_201_CREATED
        )


class DireccionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _obtener(self, request, pk):
        return get_object_or_404(
            Direccion, pk=pk, cliente=request.user, activa=True
        )

    def patch(self, request, pk):
        direccion = self._obtener(request, pk)
        serializer = DireccionSerializer(
            direccion, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        direccion = guardar_direccion(
            request.user, direccion=direccion, **serializer.validated_data
        )
        return Response(DireccionSerializer(direccion).data)

    def delete(self, request, pk):
        desactivar_direccion(self._obtener(request, pk))
        return Response({"mensaje": "Dirección eliminada correctamente."})


class ClienteBusquedaView(APIView):
    """Busca clientes activos para registrar pedidos a su nombre."""

    permission_classes = [EsOperador | EsAdmin]
    LIMITE_RESULTADOS = 20

    def get(self, request):
        clientes = User.objects.filter(rol=Rol.CLIENTE, is_active=True)

        for termino in request.query_params.get("q", "").split():
            clientes = clientes.filter(
                Q(nombre__icontains=termino)
                | Q(apellido__icontains=termino)
                | Q(email__icontains=termino)
                | Q(telefono__icontains=termino)
            )

        clientes = clientes.prefetch_related(
            Prefetch(
                "direcciones",
                queryset=Direccion.objects.filter(activa=True),
                to_attr="direcciones_activas",
            )
        ).order_by("nombre", "apellido")[: self.LIMITE_RESULTADOS]
        return Response(ClienteBusquedaSerializer(clientes, many=True).data)


# ==========================================
# MÓDULOS POR ROL (provisionales, sin datos reales todavía)
# ==========================================

class ModuloSedeView(APIView):
    permission_classes = [EsOperador]

    def get(self, request):
        return Response({"modulo": "gestion de sede"})


class ModuloCocinaView(APIView):
    permission_classes = [EsCocina]

    def get(self, request):
        return Response({"modulo": "tablero de cocina"})


class ModuloRepartidorView(APIView):
    permission_classes = [EsRepartidor]

    def get(self, request):
        return Response({"modulo": "pedidos asignados"})
