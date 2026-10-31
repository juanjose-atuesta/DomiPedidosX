from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.core.models import DiaSemana, ModeloUUID


class Sede(ModeloUUID):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitud = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class SedeUsuario(models.Model):
    """Personal operativo (operador, cocina, repartidor) asignado a una sede."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sedes_asignadas"
    )
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="personal")

    class Meta:
        verbose_name = "personal de sede"
        verbose_name_plural = "personal de sede"
        constraints = [
            models.UniqueConstraint(fields=["usuario", "sede"], name="uq_sede_usuario"),
        ]

    def __str__(self):
        return f"{self.usuario} -> {self.sede}"


class HorarioAtencion(models.Model):
    """Horario de atención de una sede por día de la semana."""

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()

    class Meta:
        verbose_name = "horario de atención"
        verbose_name_plural = "horarios de atención"
        indexes = [models.Index(fields=["sede", "dia_semana"], name="idx_horario_sede_dia")]
        constraints = [
            models.CheckConstraint(
                condition=Q(dia_semana__gte=1, dia_semana__lte=7), name="ck_horario_dia_valido"
            ),
            models.CheckConstraint(
                condition=Q(hora_cierre__gt=F("hora_apertura")), name="ck_horario_cierre_mayor"
            ),
        ]

    def __str__(self):
        return f"{self.sede} - {self.get_dia_semana_display()}"


class Feriado(models.Model):
    """Días de cierre. sede = NULL significa que aplica a todas las sedes."""

    sede = models.ForeignKey(
        Sede, on_delete=models.CASCADE, null=True, blank=True, related_name="feriados"
    )
    fecha = models.DateField(db_index=True)
    nombre = models.CharField(max_length=100)
    cerrado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fecha} {self.nombre}"
