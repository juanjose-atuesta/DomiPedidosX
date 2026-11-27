from rest_framework import serializers

from .models import ZonaCobertura
from .models import CapacidadFranja
from .services import validar_geometria
from datetime import time


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

class CapacidadFranjaSerializer(serializers.ModelSerializer):
    """Tope de pedidos simultáneos de una franja de 1 hora (HU-9.2).

    El operador envía `dia_semana`, `hora_inicio` (en punto) y
    `max_pedidos_simultaneos`. `hora_fin` la calcula el servidor (inicio + 1 h).
    La vista debe pasar la sede en el contexto: `context={"sede": sede}`.
    """

    sede_id = serializers.UUIDField(read_only=True)
    hora_fin = serializers.TimeField(read_only=True)
    max_pedidos_simultaneos = serializers.IntegerField(min_value=1)

    class Meta:
        model = CapacidadFranja
        fields = (
            "id",
            "sede_id",
            "dia_semana",
            "hora_inicio",
            "hora_fin",
            "max_pedidos_simultaneos",
            "activa",
        )
        read_only_fields = ("id", "sede_id", "hora_fin")

    def validate_hora_inicio(self, value):
        if value.minute or value.second or value.microsecond:
            raise serializers.ValidationError(
                "Las franjas son de 1 hora: la hora de inicio debe ser en punto "
                "(por ejemplo 12:00)."
            )
        return value

    def validate(self, data):
        sede = self.context["sede"]
        instancia = self.instance

        def valor(campo, defecto=None):
            if campo in data:
                return data[campo]
            return getattr(instancia, campo, defecto)

        # El tope debe estar entre 1 y el tope general de la sede (HU-9.1).
        tope_general = sede.tope_general_pedidos
        if tope_general is None:
            raise serializers.ValidationError(
                {
                    "max_pedidos_simultaneos": (
                        "El administrador debe definir primero el tope general "
                        "de la sede."
                    )
                }
            )
        tope = valor("max_pedidos_simultaneos")
        if tope is not None and tope > tope_general:
            raise serializers.ValidationError(
                {
                    "max_pedidos_simultaneos": (
                        f"El tope de la franja no puede superar el tope general "
                        f"de la sede ({tope_general})."
                    )
                }
            )

        # Franja de exactamente 1 hora. A las 23:00 termina al final del día.
        inicio = valor("hora_inicio")
        if inicio is not None:
            data["hora_fin"] = time.max if inicio.hour == 23 else time(inicio.hour + 1)

        # Una sola franja activa por sede, día y hora de inicio.
        dia = valor("dia_semana")
        if valor("activa", True) and inicio is not None and dia is not None:
            repetidas = CapacidadFranja.objects.filter(
                sede=sede, dia_semana=dia, hora_inicio=inicio, activa=True
            )
            if instancia is not None:
                repetidas = repetidas.exclude(pk=instancia.pk)
            if repetidas.exists():
                raise serializers.ValidationError(
                    {"detail": "Ya existe una franja para ese día y esa hora."}
                )
        return data