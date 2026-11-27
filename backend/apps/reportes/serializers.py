from rest_framework import serializers


class PeriodoSerializer(serializers.Serializer):
    """Período del reporte: fecha de inicio y de fin, ambas incluidas."""

    desde = serializers.DateField(
        error_messages={
            "required": "Elige la fecha de inicio.",
            "invalid": "La fecha de inicio no es válida.",
        }
    )
    hasta = serializers.DateField(
        error_messages={
            "required": "Elige la fecha de fin.",
            "invalid": "La fecha de fin no es válida.",
        }
    )

    def validate(self, datos):
        if datos["desde"] > datos["hasta"]:
            raise serializers.ValidationError(
                "La fecha de inicio no puede ser posterior a la fecha de fin."
            )
        return datos