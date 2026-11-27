from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, exigir_negocio

from .serializers import PeriodoSerializer
from .services import ventas_por_sede_y_zona


class VentasSedeZonaView(APIView):
    """El admin genera el reporte de ventas por sede y zona de su negocio (HU-10.5)."""

    permission_classes = [EsAdmin]

    def get(self, request):
        negocio = exigir_negocio(request.user)
        periodo = PeriodoSerializer(data=request.query_params)
        periodo.is_valid(raise_exception=True)
        reporte = ventas_por_sede_y_zona(negocio, **periodo.validated_data)
        return Response(reporte)
