from django.db import models
from django.db.models import ExpressionWrapper, F, Q

from apps.core.models import ModeloUUID


class InventarioSede(ModeloUUID):
    """
    Disponibilidad e inventario de un producto en una sede.
    Si NO existe fila (sede, producto), el producto no se vende en esa sede.
    """

    sede = models.ForeignKey("sedes.Sede", on_delete=models.CASCADE, related_name="inventario")
    producto = models.ForeignKey("menu.Producto", on_delete=models.CASCADE, related_name="inventario")
    disponible_en_sede = models.BooleanField(default=True)
    controla_stock = models.BooleanField(default=True)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)

    # Columnas calculadas por la base de datos: nunca quedan inconsistentes.
    agotado = models.GeneratedField(
        expression=ExpressionWrapper(
            Q(controla_stock=True, stock_actual__lte=0), output_field=models.BooleanField()
        ),
        output_field=models.BooleanField(),
        db_persist=True,
    )
    stock_bajo = models.GeneratedField(
        expression=ExpressionWrapper(
            Q(controla_stock=True, stock_actual__lte=F("stock_minimo")),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
    )

    class Meta:
        verbose_name = "inventario de sede"
        verbose_name_plural = "inventario de sedes"
        constraints = [
            models.UniqueConstraint(fields=["sede", "producto"], name="uq_inventario_sede_producto"),
        ]

    def __str__(self):
        return f"{self.producto} @ {self.sede}: {self.stock_actual}"
