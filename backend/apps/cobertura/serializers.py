from rest_framework import serializers

from .models import ZonaCobertura
from .services import validar_geometria


class ZonaCoberturaSerializer(serializers.ModelSerializer):
    sede_id = serializers.UUIDField(read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    poligono = serializers.JSONField(required=False, allow_null=True)
    tarifa_domicilio = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )
    pedido_minimo = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    tiempo_estimado_min = serializers.IntegerField(min_value=1, max_value=600)
    centro_lat = serializers.DecimalField(
        max_digits=10, decimal_places=8, min_value=-90, max_value=90,
        required=False, allow_null=True,
    )
    centro_lng = serializers.DecimalField(
        max_digits=11, decimal_places=8, min_value=-180, max_value=180,
        required=False, allow_null=True,
    )
    radio_km = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True
    )

    class Meta:
        model = ZonaCobertura
        fields = (
            "id",
            "sede_id",
            "sede_nombre",
            "nombre",
            "tipo",
            "centro_lat",
            "centro_lng",
            "radio_km",
            "poligono",
            "tarifa_domicilio",
            "pedido_minimo",
            "tiempo_estimado_min",
            "activa",
        )
        read_only_fields = ("id", "sede_id", "sede_nombre")

    def validate(self, data):
        instancia = self.instance

        def valor(campo):
            if campo in data:
                return data[campo]
            return getattr(instancia, campo, None)

        tipo = valor("tipo")
        try:
            data.update(
                validar_geometria(
                    tipo,
                    centro_lat=valor("centro_lat"),
                    centro_lng=valor("centro_lng"),
                    radio_km=valor("radio_km"),
                    poligono=valor("poligono"),
                )
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)})
        return data


class ZonaPublicaSerializer(serializers.ModelSerializer):
    """Lo que el cliente necesita saber de la zona que cubre su dirección."""

    sede_id = serializers.UUIDField(read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)

    class Meta:
        model = ZonaCobertura
        fields = (
            "id",
            "sede_id",
            "sede_nombre",
            "nombre",
            "tarifa_domicilio",
            "pedido_minimo",
            "tiempo_estimado_min",
        )
        read_only_fields = fields
