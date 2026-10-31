from django.db import models
from django.db.models import F, Q

from apps.core.models import ModeloUUID


class Promocion(ModeloUUID):
    """
    Promoción con vigencia, condiciones y cupo máximo diario.
    El cupo usado se cuenta desde Pedido.promocion (pedidos no cancelados del día).
    sede = NULL significa que aplica a todas las sedes.
    """

    sede = models.ForeignKey(
        "sedes.Sede", on_delete=models.CASCADE, null=True, blank=True, related_name="promociones"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    # guardar None (no "") cuando no haya código, para que el unique funcione
    codigo = models.CharField(max_length=50, unique=True, null=True, blank=True)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    monto_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pedido_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cupo_maximo_diario = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "promoción"
        verbose_name_plural = "promociones"
        indexes = [models.Index(fields=["activa", "fecha_inicio", "fecha_fin"], name="idx_promo_vigencia")]
        constraints = [
            models.CheckConstraint(condition=Q(fecha_fin__gte=F("fecha_inicio")), name="ck_promo_fechas"),
            models.CheckConstraint(condition=Q(cupo_maximo_diario__gt=0), name="ck_promo_cupo_positivo"),
            # exactamente uno de los dos tipos de descuento
            models.CheckConstraint(
                condition=(
                    Q(porcentaje_descuento__isnull=False, monto_descuento__isnull=True)
                    | Q(porcentaje_descuento__isnull=True, monto_descuento__isnull=False)
                ),
                name="ck_promo_un_tipo_descuento",
            ),
            models.CheckConstraint(
                condition=Q(porcentaje_descuento__isnull=True)
                | Q(porcentaje_descuento__gt=0, porcentaje_descuento__lte=100),
                name="ck_promo_porcentaje_valido",
            ),
            models.CheckConstraint(
                condition=Q(monto_descuento__isnull=True) | Q(monto_descuento__gt=0),
                name="ck_promo_monto_valido",
            ),
        ]

    def __str__(self):
        return self.nombre


class PromocionProducto(models.Model):
    """Productos/combos a los que aplica la promoción. Sin filas = aplica a todo el pedido."""

    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, related_name="productos_aplicables")
    producto = models.ForeignKey("menu.Producto", on_delete=models.CASCADE, related_name="promociones")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["promocion", "producto"], name="uq_promocion_producto"),
        ]

    def __str__(self):
        return f"{self.promocion} -> {self.producto}"
