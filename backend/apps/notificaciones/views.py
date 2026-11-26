from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsCocina, EsOperador, EsRepartidor, exigir_negocio

from .models import ConfiguracionCorreos
from .serializers import (
    ConfiguracionCorreosSerializer,
    NotificacionFiltroSerializer,
    NotificacionSerializer,
)
from .services import notificaciones_visibles_para

PERMISO_PANEL = EsOperador | EsCocina | EsAdmin | EsRepartidor
LIMITE_NOTIFICACIONES = 50


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


class NotificacionListView(APIView):
    """Alertas del panel del personal (HU-7.5 y HU-7.6).

    Filtros opcionales: ?sede=<uuid>&leida=false&tipo=pedido_cancelado.
    Responde las 50 más recientes y cuántas siguen sin leer.
    """

    permission_classes = [PERMISO_PANEL]

    def get(self, request):
        filtros = NotificacionFiltroSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        datos = filtros.validated_data

        notificaciones = notificaciones_visibles_para(request.user).select_related("sede")
        if "sede" in datos:
            notificaciones = notificaciones.filter(sede_id=datos["sede"])
        if "tipo" in datos:
            notificaciones = notificaciones.filter(tipo=datos["tipo"])
        no_leidas = notificaciones.filter(leida=False).count()
        if "leida" in datos:
            notificaciones = notificaciones.filter(leida=datos["leida"])

        return Response(
            {
                "no_leidas": no_leidas,
                "resultados": NotificacionSerializer(
                    notificaciones[:LIMITE_NOTIFICACIONES], many=True
                ).data,
            }
        )


class NotificacionDetalleView(APIView):
    """Marca una alerta como leída (o no leída): PATCH {"leida": true}."""

    permission_classes = [PERMISO_PANEL]

    def patch(self, request, pk):
        notificacion = notificaciones_visibles_para(request.user).filter(pk=pk).first()
        if notificacion is None:
            return Response(
                {"detail": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = NotificacionSerializer(notificacion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificacionMarcarLeidasView(APIView):
    """Marca como leídas todas las alertas visibles (opcional: solo de ?sede=)."""

    permission_classes = [PERMISO_PANEL]

    def post(self, request):
        filtros = NotificacionFiltroSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        notificaciones = notificaciones_visibles_para(request.user).filter(leida=False)
        if "sede" in filtros.validated_data:
            notificaciones = notificaciones.filter(sede_id=filtros.validated_data["sede"])
        return Response({"marcadas": notificaciones.update(leida=True)})
