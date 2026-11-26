from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, exigir_negocio

from .serializers import ConfiguracionCapacidadSerializer
from .services import actualizar_porcentaje_alerta


class ConfiguracionCapacidadView(APIView):
    """El admin consulta y edita el % de alerta de capacidad del negocio (HU-9.3)."""

    permission_classes = [EsAdmin]

    def get(self, request):
        negocio = exigir_negocio(request.user)
        return Response(ConfiguracionCapacidadSerializer(negocio).data)

    def patch(self, request):
        negocio = exigir_negocio(request.user)
        serializer = ConfiguracionCapacidadSerializer(negocio, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "porcentaje_alerta_capacidad" in serializer.validated_data:
            actualizar_porcentaje_alerta(
                negocio, serializer.validated_data["porcentaje_alerta_capacidad"]
            )
        return Response(ConfiguracionCapacidadSerializer(negocio).data)
