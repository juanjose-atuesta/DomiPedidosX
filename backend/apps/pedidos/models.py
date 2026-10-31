import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.core.models import Timestamped


class EstadoPedido(models.TextChoices):
    RECIBIDO = "recibido", "Recibido"
    EN_PREPARACION = "en_preparacion", "En preparación"
    LISTO_DESPACHO = "listo_despacho", "Listo para despacho"
    EN_CAMINO = "en_camino", "En camino"
    ENTREGADO = "entregado", "Entregado"
    CANCELADO = "cancelado", "Cancelado"


class MetodoPago(models.TextChoices):  # el pago es simulado
    EFECTIVO = "efectivo", "Efectivo"
    TARJETA = "tarjeta", "Tarjeta"
    TRANSFERENCIA = "transferencia", "Transferencia"


class TipoPedido(models.TextChoices):
    DOMICILIO = "domicilio", "Domicilio"
    RECOGER = "recoger", "Recoger en sede"


class CanalPedido(models.TextChoices):
    WEB = "web", "Web"
    TELEFONO = "telefono", "Telefónico"
    MOSTRADOR = "mostrador", "Mostrador"


class Pedido(Timestamped):
    # Clave numérica autoincremental: es el número de pedido legible (#1042)
    id = models.BigAutoField(primary_key=True)

    # Quién pide y quién lo registró
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",  # NULL = cliente sin cuenta (pedido de mostrador)
    )
    cliente_nombre = models.CharField(max_length=200)  # snapshot
    cliente_telefono = models.CharField(max_length=20)  # snapshot
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos_creados",  # el cliente o el operador que lo registró
    )
    canal = models.CharField(
        max_length=20, choices=CanalPedido.choices, default=CanalPedido.WEB
    )
    tipo = models.CharField(
        max_length=20, choices=TipoPedido.choices, default=TipoPedido.DOMICILIO
    )

    # Dónde se prepara y a dónde va
    sede = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="pedidos"
    )
    direccion = models.ForeignKey(
        "usuarios.Direccion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    # Snapshot de la dirección: si el cliente edita o borra la suya, el pedido no se pierde
    direccion_entrega = models.TextField(blank=True)
    entrega_lat = models.DecimalField(
        max_digits=10, decimal_places=8, null=True, blank=True
    )
    entrega_lng = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    zona = models.ForeignKey(
        "cobertura.ZonaCobertura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="entregas",
    )
    promocion = models.ForeignKey(
        "promociones.Promocion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )

    # Estado y pago
    estado = models.CharField(
        max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.RECIBIDO
    )
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    costo_domicilio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    tiempo_estimado_entrega = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    motivo_cancelacion = models.TextField(blank=True)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(
                fields=["sede", "estado"], name="idx_pedido_sede_estado"
            ),  # tablero de cocina
            models.Index(
                fields=["creado_en"], name="idx_pedido_creado"
            ),  # reportes, "pedidos del día"
            models.Index(  # cupo diario de promociones
                fields=["promocion", "creado_en"],
                condition=Q(promocion__isnull=False),
                name="idx_pedido_promocion",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=0), name="ck_pedido_subtotal"
            ),
            models.CheckConstraint(
                condition=Q(costo_domicilio__gte=0), name="ck_pedido_domicilio"
            ),
            models.CheckConstraint(
                condition=Q(descuento__gte=0), name="ck_pedido_descuento"
            ),
            models.CheckConstraint(
                condition=Q(
                    total=F("subtotal") + F("costo_domicilio") - F("descuento")
                ),
                name="ck_pedido_total_consistente",
            ),
            # un pedido a domicilio debe tener dirección de entrega completa
            models.CheckConstraint(
                condition=~Q(tipo="domicilio")
                | (
                    ~Q(direccion_entrega="")
                    & Q(entrega_lat__isnull=False)
                    & Q(entrega_lng__isnull=False)
                ),
                name="ck_pedido_domicilio_con_direccion",
            ),
        ]

    def __str__(self):
        return f"Pedido #{self.pk} ({self.estado})"


class DetallePedido(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "menu.Producto", on_delete=models.PROTECT, related_name="+"
    )
    nombre_producto = models.CharField(max_length=150)  # snapshot
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # snapshot, sin opciones
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # incluye opciones
    notas_producto = models.TextField(blank=True)

    class Meta:
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad__gt=0), name="ck_detalle_cantidad"
            ),
            models.CheckConstraint(
                condition=Q(precio_unitario__gte=0), name="ck_detalle_precio"
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0), name="ck_detalle_subtotal"
            ),
        ]

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto}"


class DetallePedidoOpcion(models.Model):
    """Opciones elegidas en una línea del pedido (snapshot de nombre y precio)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    detalle = models.ForeignKey(
        DetallePedido, on_delete=models.CASCADE, related_name="opciones"
    )
    opcion = models.ForeignKey(
        "menu.OpcionProducto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    nombre_opcion = models.CharField(max_length=100)
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "opción de detalle"
        verbose_name_plural = "opciones de detalle"

    def __str__(self):
        return self.nombre_opcion


class HistorialEstado(models.Model):
    """
    Trazabilidad: tiempos por etapa y desempeño de repartidores.
    El backend crea una fila cada vez que cambia el estado (en la misma transacción).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="historial"
    )
    estado = models.CharField(max_length=20, choices=EstadoPedido.choices)
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    fecha_hora = models.DateTimeField(default=timezone.now)
    comentario = models.TextField(blank=True)

    class Meta:
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"
        ordering = ["fecha_hora"]
        indexes = [
            models.Index(
                fields=["pedido", "fecha_hora"], name="idx_historial_pedido_fecha"
            )
        ]

    def __str__(self):
        return f"Pedido #{self.pedido_id} -> {self.estado}"
