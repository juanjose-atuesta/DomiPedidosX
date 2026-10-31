from django.db import models
from django.db.models import F, Q

from apps.core.models import ModeloUUID


class Categoria(ModeloUUID):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Producto(ModeloUUID):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(blank=True)  # ej: URL de Cloudinary
    tiempo_preparacion_min = models.PositiveIntegerField(default=15)
    es_combo = models.BooleanField(default=False)
    disponible = models.BooleanField(default=True)  # interruptor global del admin

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(precio_base__gte=0), name="ck_producto_precio_no_negativo"),
            models.CheckConstraint(condition=Q(tiempo_preparacion_min__gt=0), name="ck_producto_tiempo_positivo"),
        ]

    def __str__(self):
        return self.nombre


class ProductoCombo(models.Model):
    """Composición de un combo (un combo es un Producto con es_combo=True)."""

    combo = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="componentes")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="en_combos")
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["combo", "producto"], name="uq_combo_producto"),
            models.CheckConstraint(condition=~Q(combo=F("producto")), name="ck_combo_no_se_contiene"),
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="ck_combo_cantidad_positiva"),
        ]

    def __str__(self):
        return f"{self.combo} incluye {self.cantidad} x {self.producto}"


class TipoGrupoOpcion(models.TextChoices):
    TAMANO = "tamano", "Tamaño"
    ADICION = "adicion", "Adición"
    EXCLUIBLE = "excluible", "Ingrediente excluible"


class GrupoOpcion(ModeloUUID):
    """Grupo de opciones de un producto: 'Tamaño', 'Adiciones', 'Quitar ingredientes'."""

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="grupos_opcion")
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TipoGrupoOpcion.choices)
    obligatorio = models.BooleanField(default=False)
    max_selecciones = models.PositiveSmallIntegerField(default=1)
    orden = models.IntegerField(default=0)

    class Meta:
        verbose_name = "grupo de opciones"
        verbose_name_plural = "grupos de opciones"
        ordering = ["orden"]
        constraints = [
            models.CheckConstraint(condition=Q(max_selecciones__gte=1), name="ck_grupo_max_selecciones"),
        ]

    def __str__(self):
        return f"{self.producto} - {self.nombre}"


class OpcionProducto(ModeloUUID):
    """Opción concreta: 'Grande', 'Queso extra', 'Sin cebolla'."""

    grupo = models.ForeignKey(GrupoOpcion, on_delete=models.CASCADE, related_name="opciones")
    nombre = models.CharField(max_length=100)
    precio_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)

    class Meta:
        verbose_name = "opción de producto"
        verbose_name_plural = "opciones de producto"
        ordering = ["orden"]
        constraints = [
            models.CheckConstraint(condition=Q(precio_adicional__gte=0), name="ck_opcion_precio_no_negativo"),
        ]

    def __str__(self):
        return self.nombre
