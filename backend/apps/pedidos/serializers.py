from rest_framework import serializers

from apps.menu.models import Producto
from apps.sedes.models import Sede

from .models import (
    CanalPedido,
    DetallePedido,
    DetallePedidoOpcion,
    MetodoPago,
    Pedido,
    TipoPedido,
)


class DetallePedidoInputSerializer(serializers.Serializer):
    producto_id = serializers.PrimaryKeyRelatedField(
        source="producto",
        queryset=Producto.objects.all(),
    )
    cantidad = serializers.IntegerField(min_value=1)
    notas_producto = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    opciones = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=list,
    )


class PedidoCreateSerializer(serializers.Serializer):
    sede_id = serializers.PrimaryKeyRelatedField(
        source="sede",
        queryset=Sede.objects.filter(activa=True),
    )
    cliente_nombre = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )
    cliente_telefono = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
    )
    canal = serializers.ChoiceField(
        choices=CanalPedido.choices,
        required=False,
        default=CanalPedido.WEB,
    )
    tipo = serializers.ChoiceField(
        choices=TipoPedido.choices,
        required=False,
        default=TipoPedido.RECOGER,
    )
    metodo_pago = serializers.ChoiceField(
        choices=MetodoPago.choices,
        required=False,
        default=MetodoPago.EFECTIVO,
    )
    direccion_entrega = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    entrega_lat = serializers.DecimalField(
        max_digits=10,
        decimal_places=8,
        required=False,
        allow_null=True,
    )
    entrega_lng = serializers.DecimalField(
        max_digits=11,
        decimal_places=8,
        required=False,
        allow_null=True,
    )
    costo_domicilio = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        default=0,
    )
    descuento = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        default=0,
    )
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    detalles = DetallePedidoInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        if attrs.get("tipo") == TipoPedido.DOMICILIO and (
            not attrs.get("direccion_entrega")
            or attrs.get("entrega_lat") is None
            or attrs.get("entrega_lng") is None
        ):
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Los pedidos a domicilio requieren "
                        "direccion_entrega, entrega_lat y entrega_lng."
                    )
                }
            )

        return attrs


class DetallePedidoOpcionSalidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedidoOpcion
        fields = ("id", "nombre_opcion", "precio_adicional")
        read_only_fields = fields


class DetallePedidoSalidaSerializer(serializers.ModelSerializer):
    producto_id = serializers.UUIDField(read_only=True)
    opciones = DetallePedidoOpcionSalidaSerializer(many=True, read_only=True)

    class Meta:
        model = DetallePedido
        fields = (
            "id",
            "producto_id",
            "nombre_producto",
            "cantidad",
            "precio_unitario",
            "subtotal",
            "notas_producto",
            "opciones",
        )
        read_only_fields = fields


class PedidoSerializer(serializers.ModelSerializer):
    sede_id = serializers.UUIDField(read_only=True)
    cliente_id = serializers.UUIDField(read_only=True, allow_null=True)
    detalles = DetallePedidoSalidaSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id",
            "cliente_id",
            "cliente_nombre",
            "cliente_telefono",
            "creado_por",
            "canal",
            "tipo",
            "sede_id",
            "estado",
            "metodo_pago",
            "subtotal",
            "costo_domicilio",
            "descuento",
            "total",
            "tiempo_estimado_entrega",
            "observaciones",
            "creado_en",
            "detalles",
        )
        read_only_fields = fields
