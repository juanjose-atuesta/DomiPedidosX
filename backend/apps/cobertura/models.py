from django.db import models
from django.db.models import F, Q

from apps.core.models import DiaSemana, ModeloUUID


class TipoCobertura(models.TextChoices):
    RADIO = "radio", "Radio"
    POLIGONO = "poligono", "Polígono"


class ZonaCobertura(ModeloUUID):
    sede = models.ForeignKey("sedes.Sede", on_delete=models.CASCADE, related_name="zonas")
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TipoCobertura.choices)
    # tipo = radio
    centro_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    centro_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    radio_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # tipo = poligono: lista de puntos [[lat, lng], [lat, lng], ...]
    poligono = models.JSONField(null=True, blank=True)
    tarifa_domicilio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tiempo_estimado_min = models.PositiveIntegerField()
    pedido_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "zona de cobertura"
        verbose_name_plural = "zonas de cobertura"
        constraints = [
            models.CheckConstraint(condition=Q(tarifa_domicilio__gte=0), name="ck_zona_tarifa_no_negativa"),
            models.CheckConstraint(condition=Q(pedido_minimo__gte=0), name="ck_zona_minimo_no_negativo"),
            models.CheckConstraint(condition=Q(tiempo_estimado_min__gt=0), name="ck_zona_tiempo_positivo"),
            models.CheckConstraint(
                condition=(
                    Q(tipo="radio", centro_lat__isnull=False, centro_lng__isnull=False, radio_km__gt=0)
                    | Q(tipo="poligono", poligono__isnull=False)
                ),
                name="ck_zona_geometria_completa",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.sede})"


class CapacidadFranja(models.Model):
    """Tope de pedidos simultáneos por sede, día de la semana y franja horaria."""

    sede = models.ForeignKey("sedes.Sede", on_delete=models.CASCADE, related_name="franjas_capacidad")
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    max_pedidos_simultaneos = models.PositiveIntegerField()
    umbral_alerta_pct = models.PositiveSmallIntegerField(default=80)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "franja de capacidad"
        verbose_name_plural = "franjas de capacidad"
        indexes = [models.Index(fields=["sede", "dia_semana"], name="idx_capacidad_sede_dia")]
        constraints = [
            models.CheckConstraint(condition=Q(dia_semana__gte=1, dia_semana__lte=7), name="ck_capacidad_dia_valido"),
            models.CheckConstraint(condition=Q(hora_fin__gt=F("hora_inicio")), name="ck_capacidad_fin_mayor"),
            models.CheckConstraint(condition=Q(max_pedidos_simultaneos__gt=0), name="ck_capacidad_max_positivo"),
            models.CheckConstraint(
                condition=Q(umbral_alerta_pct__gte=1, umbral_alerta_pct__lte=100), name="ck_capacidad_umbral_valido"
            ),
        ]

    def __str__(self):
        return f"{self.sede} {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"
