import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class TipoNotificacion(models.TextChoices):
    PEDIDO_CONFIRMADO = "pedido_confirmado", "Pedido confirmado"
    CAMBIO_ESTADO = "cambio_estado", "Cambio de estado"
    PEDIDO_CANCELADO = "pedido_cancelado", "Pedido cancelado"
    REPARTIDOR_ASIGNADO = "repartidor_asignado", "Repartidor asignado"
    PEDIDO_EN_CAMINO = "pedido_en_camino", "Pedido en camino"
    ALERTA_CAPACIDAD = "alerta_capacidad", "Alerta de capacidad"
    ALERTA_STOCK_BAJO = "alerta_stock_bajo", "Alerta de stock bajo"


class CanalNotificacion(models.TextChoices):
    CORREO = "correo", "Correo"
    SISTEMA = "sistema", "Sistema (panel)"


class EstadoEnvio(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    ENVIADO = "enviado", "Enviado"
    FALLIDO = "fallido", "Fallido"


class Notificacion(models.Model):
    """Registro de correos enviados y alertas mostradas en el panel."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="notificaciones",  # destinatario (NULL = alerta general de la sede)
    )
    sede = models.ForeignKey(
        "sedes.Sede", on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones"
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido", on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=30, choices=TipoNotificacion.choices)
    canal = models.CharField(max_length=10, choices=CanalNotificacion.choices)
    asunto = models.CharField(max_length=200, blank=True)
    mensaje = models.TextField()
    estado_envio = models.CharField(
        max_length=10, choices=EstadoEnvio.choices, default=EstadoEnvio.PENDIENTE
    )
    intentos = models.PositiveSmallIntegerField(default=0)
    leida = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    enviado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["usuario", "leida"], name="idx_notif_usuario_leida"),
            models.Index(
                fields=["estado_envio"],
                condition=Q(estado_envio="pendiente"),
                name="idx_notif_pendientes",
            ),
        ]

    def __str__(self):
        return f"{self.tipo} ({self.estado_envio})"
