from rest_framework import serializers

from .models import Feriado, HorarioAtencion, Sede
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
            "asignacion_automatica_repartidor",
            "horarios",
        )
        read_only_fields = ("id", "activa")

    def validate_horarios(self, value):
        try:
            validar_horarios(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return value


class FeriadoSerializer(serializers.ModelSerializer):
    """Feriado del negocio. Sin `sedes_ids` aplica a todas sus sedes."""

    sedes_ids = serializers.PrimaryKeyRelatedField(
        source="sedes",
        many=True,
        required=False,
        queryset=Sede.objects.all(),
    )
    sedes = serializers.SerializerMethodField()
    aplica_a_todas = serializers.SerializerMethodField()

    class Meta:
        model = Feriado
        fields = ("id", "fecha", "nombre", "sedes_ids", "sedes", "aplica_a_todas")
        read_only_fields = ("id",)

    def get_sedes(self, obj):
        return [{"id": str(s.pk), "nombre": s.nombre} for s in obj.sedes.all()]

    def get_aplica_a_todas(self, obj):
        return not obj.sedes.exists()

    def validate_sedes_ids(self, sedes):
        negocio_id = self.context["negocio_id"]
        if any(sede.negocio_id != negocio_id for sede in sedes):
            raise serializers.ValidationError(
                "Una o más sedes no pertenecen a tu negocio."
            )
        return sedes
