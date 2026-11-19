from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, exigir_negocio

from .models import ConfiguracionCorreos
from .serializers import ConfiguracionCorreosSerializer


class ConfiguracionCorreosView(APIView):
    """Correos al cliente que el negocio activa o desactiva por evento (HU-8.10)."""

    permission_classes = [EsAdmin]

    def get(self, request):
        negocio = exigir_negocio(request.user)
        config, _ = ConfiguracionCorreos.objects.get_or_create(negocio=negocio)
        return Response(ConfiguracionCorreosSerializer(config).data)

    def patch(self, request):
        negocio = exigir_negocio(request.user)
        config, _ = ConfiguracionCorreos.objects.get_or_create(negocio=negocio)
        serializer = ConfiguracionCorreosSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
