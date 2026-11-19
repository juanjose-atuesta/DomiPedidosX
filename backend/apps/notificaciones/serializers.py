from rest_framework import serializers

from .models import ConfiguracionCorreos


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
