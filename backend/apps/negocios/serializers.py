from rest_framework import serializers

from .models import Negocio


class ConfiguracionCapacidadSerializer(serializers.ModelSerializer):
    """Porcentaje de alerta de capacidad del negocio (HU-9.3)."""

    porcentaje_alerta_capacidad = serializers.IntegerField(
        min_value=1,
        max_value=100,
        error_messages={
            "min_value": "El porcentaje debe estar entre 1 y 100.",
            "max_value": "El porcentaje debe estar entre 1 y 100.",
            "invalid": "El porcentaje debe ser un número entero.",
        },
    )
    sedes_afectadas = serializers.SerializerMethodField()

    class Meta:
        model = Negocio
        fields = ("porcentaje_alerta_capacidad", "sedes_afectadas", "actualizado_en")
        read_only_fields = ("sedes_afectadas", "actualizado_en")

    def get_sedes_afectadas(self, negocio):
        return negocio.sedes.count()
