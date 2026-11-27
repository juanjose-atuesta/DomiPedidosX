from rest_framework import serializers

from .models import ConfiguracionCorreos, Notificacion


class ConfiguracionCorreosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionCorreos
        fields = (
            "confirmacion",
            "cambio_estado",
            "cancelacion",
            "asignacion_repartidor",
            "actualizado_en",
        )
        read_only_fields = ("actualizado_en",)


class NotificacionSerializer(serializers.ModelSerializer):
    """Alerta de panel. Solo `leida` se puede cambiar."""

    sede_id = serializers.UUIDField(read_only=True, allow_null=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default=None)
    pedido_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Notificacion
        fields = (
            "id",
            "tipo",
            "asunto",
            "mensaje",
            "sede_id",
            "sede_nombre",
            "pedido_id",
            "leida",
            "creado_en",
        )
        read_only_fields = tuple(f for f in fields if f != "leida")


class NotificacionFiltroSerializer(serializers.Serializer):
    sede = serializers.UUIDField(required=False)
    # En query params un BooleanField ausente se leería como False.
    leida = serializers.ChoiceField(choices=["true", "false"], required=False)
    tipo = serializers.ChoiceField(
        choices=Notificacion._meta.get_field("tipo").choices, required=False
    )

    def validate_leida(self, value):
        return value == "true"
