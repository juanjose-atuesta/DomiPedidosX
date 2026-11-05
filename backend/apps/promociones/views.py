from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador
from apps.usuarios.models import Rol

from .models import Promocion
from .serializers import PromocionSerializer
from .services import (
    actualizar_promocion,
    crear_promocion,
    desactivar_promocion,
)

PERMISO_GESTION = EsOperador | EsAdmin


def _es_gestor(request):
    usuario = getattr(request, "user", None)
    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
        and usuario.rol in (Rol.OPERADOR, Rol.ADMIN)
    )


def _obtener_promocion(pk):
    try:
        return (
            Promocion.objects.select_related("sede")
            .prefetch_related("productos_aplicables__producto")
            .get(pk=pk)
        )
    except (Promocion.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _vigente(promocion):
    hoy = timezone.localdate()
    return promocion.fecha_inicio <= hoy <= promocion.fecha_fin


def _datos_promocion(validated_data):
    datos = dict(validated_data)
    if "sede" in datos:
        sede = datos.pop("sede")
        datos["sede_id"] = getattr(sede, "pk", None)
    return datos


class PromocionListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request):
        hoy = timezone.localdate()
        promociones = (
            Promocion.objects.filter(
                activa=True,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy,
            )
            .select_related("sede")
            .prefetch_related("productos_aplicables__producto")
            .order_by("fecha_fin", "nombre")
        )
        return Response(PromocionSerializer(promociones, many=True).data)

    def post(self, request):
        serializer = PromocionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = _datos_promocion(serializer.validated_data)
        try:
            promocion = crear_promocion(**datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            PromocionSerializer(promocion).data,
            status=status.HTTP_201_CREATED,
        )


class PromocionDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        promocion = _obtener_promocion(pk)
        if promocion is None:
            return Response(
                {"detail": "Promocion no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            not promocion.activa or not _vigente(promocion)
        ) and not _es_gestor(request):
            return Response(
                {"detail": "Promocion no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(PromocionSerializer(promocion).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        promocion = _obtener_promocion(pk)
        if promocion is None:
            return Response(
                {"detail": "Promocion no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PromocionSerializer(
            promocion, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        datos = _datos_promocion(serializer.validated_data)
        try:
            promocion = actualizar_promocion(pk, **datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(PromocionSerializer(promocion).data)

    def delete(self, request, pk):
        promocion = _obtener_promocion(pk)
        if promocion is None:
            return Response(
                {"detail": "Promocion no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        desactivar_promocion(pk)
        return Response(
            {"mensaje": "Promocion desactivada correctamente."}
        )
