from rest_framework import serializers

from .models import HorarioAtencion, Sede
from .services import validar_horarios


class HorarioAtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioAtencion
        fields = ("dia_semana", "hora_apertura", "hora_cierre")

    def validate(self, data):
        apertura = data.get("hora_apertura")
        cierre = data.get("hora_cierre")

        if apertura is not None and cierre is not None and cierre <= apertura:
            raise serializers.ValidationError(
                {
                    "hora_cierre": (
                        "La hora de cierre debe ser mayor que la hora "
                        "de apertura."
                    )
                }
            )
        return data


class SedeSerializer(serializers.ModelSerializer):
    horarios = HorarioAtencionSerializer(many=True, required=False)
    negocio_id = serializers.UUIDField(read_only=True)
    negocio_nombre = serializers.CharField(source="negocio.nombre", read_only=True)

    class Meta:
        model = Sede
        fields = (
            "id",
            "negocio_id",
            "negocio_nombre",
            "nombre",
            "direccion",
            "telefono",
            "latitud",
            "longitud",
            "activa",
            "horarios",
        )
        read_only_fields = ("id", "activa")

    def validate_horarios(self, value):
        try:
            validar_horarios(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return value
