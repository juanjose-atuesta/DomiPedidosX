from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador, exigir_gestion_sede
from apps.pedidos.models import Pedido
from apps.pedidos.serializers import PedidoSerializer
from apps.sedes.models import Sede

from .serializers import (
    AsignarRepartidorSerializer,
    ConfiguracionRepartoSerializer,
    RepartidorSerializer,
)
from .services import asignar_pendientes, asignar_repartidor, repartidores_de_sede

PERMISO = EsOperador | EsAdmin


def _sede(request, sede_id):
    """Sede que el usuario gestiona; otra cualquiera responde 403/404."""
    sede = Sede.objects.filter(pk=sede_id).first()
    if sede is None:
        return None
    exigir_gestion_sede(request.user, sede)
    return sede


class RepartidoresSedeView(APIView):
    """Repartidores de la sede con su estado: disponible u ocupado (HU-6.5)."""

    permission_classes = [PERMISO]

    def get(self, request, sede_id):
        sede = _sede(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        repartidores = repartidores_de_sede(sede)
        return Response(
            {
                "sede_id": str(sede.pk),
                "asignacion_automatica_repartidor": sede.asignacion_automatica_repartidor,
                "repartidores": RepartidorSerializer(repartidores, many=True).data,
            }
        )


class ConfiguracionRepartoView(APIView):
    """Interruptor de asignación automática de la sede (HU-6.6).

    Al activarlo se reparten de inmediato los domicilios que ya esperaban.
    """

    permission_classes = [PERMISO]

    def patch(self, request, sede_id):
        sede = _sede(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConfiguracionRepartoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sede.asignacion_automatica_repartidor = serializer.validated_data[
                "asignacion_automatica_repartidor"
            ]
            sede.save(update_fields=["asignacion_automatica_repartidor", "actualizado_en"])
            asignar_pendientes(sede)
        return Response(
            {"asignacion_automatica_repartidor": sede.asignacion_automatica_repartidor}
        )


class AsignarRepartidorView(APIView):
    """El operador asigna un repartidor disponible a un domicilio listo (HU-6.5)."""

    permission_classes = [PERMISO]

    def post(self, request, pk):
        pedido = Pedido.objects.filter(pk=pk).first()
        if pedido is None:
            return Response({"detail": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        exigir_gestion_sede(request.user, pedido.sede_id)
        serializer = AsignarRepartidorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pedido = asignar_repartidor(
                pk,
                serializer.validated_data["repartidor_id"],
                asignado_por=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PedidoSerializer(pedido).data)
