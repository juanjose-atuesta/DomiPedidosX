from rest_framework import serializers

from apps.menu.models import Producto

from .models import InventarioSede


class InventarioSedeSerializer(serializers.ModelSerializer):
    sede_id = serializers.UUIDField(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        source="producto",
        queryset=Producto.objects.all(),
    )
    producto_nombre = serializers.CharField(
        source="producto.nombre", read_only=True
    )
    stock_actual = serializers.IntegerField(min_value=0, required=False)
    stock_minimo = serializers.IntegerField(min_value=0, required=False)
    agotado = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventarioSede
        fields = (
            "id",
            "sede_id",
            "producto_id",
            "producto_nombre",
            "disponible_en_sede",
            "controla_stock",
            "stock_actual",
            "stock_minimo",
            "agotado",
            "stock_bajo",
        )
        read_only_fields = ("id", "sede_id", "agotado", "stock_bajo")
