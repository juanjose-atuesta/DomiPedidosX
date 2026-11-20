from django.db import models

from apps.core.models import ModeloUUID


class Negocio(ModeloUUID):
    """Restaurante dueño de sus sedes, menú, promociones y personal."""

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)  # ej: URL de Cloudinary
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "negocio"
        verbose_name_plural = "negocios"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def fecha_creacion(self):
        return self.creado_en
