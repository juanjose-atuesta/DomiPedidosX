import uuid

from django.db import models


class Timestamped(models.Model):
    """Agrega fechas de creación y actualización automáticas."""

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ModeloUUID(Timestamped):
    """Base de casi todas las tablas: clave primaria UUID + fechas."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class DiaSemana(models.IntegerChoices):
    LUNES = 1, "Lunes"
    MARTES = 2, "Martes"
    MIERCOLES = 3, "Miércoles"
    JUEVES = 4, "Jueves"
    VIERNES = 5, "Viernes"
    SABADO = 6, "Sábado"
    DOMINGO = 7, "Domingo"


class ConfiguracionGlobal(models.Model):
    """Parámetros globales clave/valor. Ej: 'umbral_alerta_capacidad_pct' = '80'."""

    clave = models.CharField(max_length=100, primary_key=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuración global"
        verbose_name_plural = "configuración global"

    def __str__(self):
        return f"{self.clave} = {self.valor}"
