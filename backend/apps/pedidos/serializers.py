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
        queryset=Sede.objects.filter(activa=True, negocio__activo=True),
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
    # El costo de domicilio y el descuento NO se reciben: el servidor los
    # calcula con la zona de cobertura y la promoción.
    codigo_promocion = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default="",
    )
    promocion_id = serializers.UUIDField(required=False, allow_null=True)
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


class CancelarPedidoSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        max_length=300, required=False, allow_blank=True, default=""
    )


class RechazarPedidoSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        min_length=10,
        max_length=300,
        error_messages={
            "min_length": "El motivo del rechazo debe tener al menos 10 caracteres.",
            "blank": "El motivo del rechazo es obligatorio.",
            "required": "El motivo del rechazo es obligatorio.",
        },
    )


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
    negocio_nombre = serializers.CharField(source="sede.negocio.nombre", read_only=True)
    cliente_id = serializers.UUIDField(read_only=True, allow_null=True)
    detalles = DetallePedidoSalidaSerializer(many=True, read_only=True)
    estados_siguientes = serializers.SerializerMethodField()
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True, default=None)
    promocion_nombre = serializers.CharField(
        source="promocion.nombre", read_only=True, default=None
    )
    puede_cancelar = serializers.SerializerMethodField()
    repartidor_id = serializers.UUIDField(read_only=True, allow_null=True)
    repartidor_nombre = serializers.SerializerMethodField()
    repartidor_lat = serializers.SerializerMethodField()
    repartidor_lng = serializers.SerializerMethodField()
    esperando_repartidor = serializers.SerializerMethodField()
    asignacion_automatica = serializers.BooleanField(
        source="sede.asignacion_automatica_repartidor", read_only=True
    )

    def get_puede_cancelar(self, pedido):
        return pedido.estado == EstadoPedido.RECIBIDO

    def get_repartidor_nombre(self, pedido):
        return pedido.repartidor.nombre_completo if pedido.repartidor_id else None

    def get_repartidor_lat(self, pedido):
        if pedido.repartidor_id and hasattr(pedido.repartidor, 'perfil_repartidor'):
            return float(pedido.repartidor.perfil_repartidor.latitud) if pedido.repartidor.perfil_repartidor.latitud else None
        return None

    def get_repartidor_lng(self, pedido):
        if pedido.repartidor_id and hasattr(pedido.repartidor, 'perfil_repartidor'):
            return float(pedido.repartidor.perfil_repartidor.longitud) if pedido.repartidor.perfil_repartidor.longitud else None
        return None

    def get_esperando_repartidor(self, pedido):
        """Domicilio listo que nadie lleva todavía."""
        return (
            pedido.tipo == TipoPedido.DOMICILIO
            and pedido.estado == EstadoPedido.LISTO_DESPACHO
            and pedido.repartidor_id is None
        )

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
            "negocio_nombre",
            "direccion_entrega",
            "estado",
            "estados_siguientes",
            "puede_cancelar",
            "motivo_cancelacion",
            "zona_nombre",
            "promocion_nombre",
            "repartidor_id",
            "repartidor_nombre",
            "repartidor_lat",
            "repartidor_lng", 
            "esperando_repartidor",
            "asignacion_automatica",
            "metodo_pago",
            "subtotal",
            "costo_domicilio",
            "descuento",
            "total",
            "tiempo_estimado_entrega",
            "observaciones",
            "creado_en",
            "detalles",
            "tiempo_estimado_entrega",
            "ubicacion_repartidor_lat",
            "ubicacion_repartidor_lng",
            "ubicacion_actualizada_en",
            "observaciones",
        )
        read_only_fields = fields

class UbicacionRepartidorSerializer(serializers.Serializer):
    latitud = serializers.FloatField(min_value=-90, max_value=90)
    longitud = serializers.FloatField(min_value=-180, max_value=180)