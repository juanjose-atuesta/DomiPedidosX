from rest_framework import serializers

from apps.menu.models import Producto
from apps.sedes.models import Sede
from apps.usuarios.models import Rol, User

from .models import (
    CanalPedido,
    DetallePedido,
    DetallePedidoOpcion,
    EstadoPedido,
    MetodoPago,
    Pedido,
    TipoPedido,
)
from .services import estados_siguientes

CANTIDAD_MAXIMA_POR_LINEA = 10


class DetallePedidoInputSerializer(serializers.Serializer):
    producto_id = serializers.PrimaryKeyRelatedField(
        source="producto",
        queryset=Producto.objects.all(),
    )
    cantidad = serializers.IntegerField(
        min_value=1, max_value=CANTIDAD_MAXIMA_POR_LINEA
    )
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
    # Solo lo usan operador y admin; si lo envía un cliente se ignora.
    cliente_id = serializers.PrimaryKeyRelatedField(
        source="cliente",
        queryset=User.objects.filter(rol=Rol.CLIENTE, is_active=True),
        required=False,
        allow_null=True,
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


class PedidoFiltroSerializer(serializers.Serializer):
    sede = serializers.UUIDField(required=False)
    # Uno o varios estados separados por coma: ?estado=recibido,en_preparacion
    estado = serializers.CharField(required=False)
    fecha = serializers.DateField(required=False)

    def validate_estado(self, value):
        estados = [estado.strip() for estado in value.split(",") if estado.strip()]
        if not estados or any(e not in EstadoPedido.values for e in estados):
            raise serializers.ValidationError("El estado no es valido.")
        return estados


class CambioEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoPedido.choices)
    comentario = serializers.CharField(required=False, allow_blank=True)


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
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    cliente_id = serializers.UUIDField(read_only=True, allow_null=True)
    detalles = DetallePedidoSalidaSerializer(many=True, read_only=True)
    estados_siguientes = serializers.SerializerMethodField()

    def get_estados_siguientes(self, pedido):
        return estados_siguientes(pedido)

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
            "sede_nombre",
            "direccion_entrega",
            "estado",
            "estados_siguientes",
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
