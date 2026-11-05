from decimal import Decimal

from rest_framework import serializers

from apps.sedes.models import Sede

from .models import Promocion, PromocionProducto


class PromocionProductoSerializer(serializers.ModelSerializer):
    producto_id = serializers.UUIDField(read_only=True)
    producto_nombre = serializers.CharField(
        source="producto.nombre", read_only=True
    )

    class Meta:
        model = PromocionProducto
        fields = ("producto_id", "producto_nombre")


class PromocionSerializer(serializers.ModelSerializer):
    sede_id = serializers.PrimaryKeyRelatedField(
        source="sede",
        queryset=Sede.objects.all(),
        required=False,
        allow_null=True,
    )
    porcentaje_descuento = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("100"),
        required=False,
        allow_null=True,
    )
    monto_descuento = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
        allow_null=True,
    )
    pedido_minimo = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
    )
    cupo_maximo_diario = serializers.IntegerField(
        min_value=1,
        required=True,
    )
    fecha_inicio = serializers.DateField(required=True)
    fecha_fin = serializers.DateField(required=True)
    productos_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    productos = PromocionProductoSerializer(
        source="productos_aplicables",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Promocion
        fields = (
            "id",
            "sede_id",
            "nombre",
            "descripcion",
            "codigo",
            "porcentaje_descuento",
            "monto_descuento",
            "pedido_minimo",
            "cupo_maximo_diario",
            "fecha_inicio",
            "fecha_fin",
            "activa",
            "productos_ids",
            "productos",
        )
        read_only_fields = ("id", "activa", "productos")
