from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import ModeloUUID


class Negocio(ModeloUUID):
    """Restaurante dueño de sus sedes, menú, promociones y personal."""

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)  # ej: URL de Cloudinary
    activo = models.BooleanField(default=True)
    # HU-9.3: al llegar a este % del tope de capacidad se alerta a la sede.
    # Es del negocio, así que aplica a todas sus sedes.
    porcentaje_alerta_capacidad = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )

    class Meta:
        verbose_name = "negocio"
        verbose_name_plural = "negocios"
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=Q(porcentaje_alerta_capacidad__gte=1)
                & Q(porcentaje_alerta_capacidad__lte=100),
                name="ck_negocio_porcentaje_alerta",
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def fecha_creacion(self):
        return self.creado_en
