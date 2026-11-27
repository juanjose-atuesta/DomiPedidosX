"""Capacidad de las sedes: bloqueo de nuevos pedidos cuando la sede está llena (HU-9.5).

El tope vigente sale de la franja de capacidad activa para el día y la hora
(`CapacidadFranja`, HU-9.1/9.2) y, si no hay ninguna, del tope general de la
sede (`Sede.tope_general_pedidos`). Sin tope configurado no se bloquea nada.
"""

from dataclasses import dataclass
from datetime import datetime, time

from django.utils import timezone

from .models import EstadoPedido, Pedido

MENSAJE_CAPACIDAD_LLENA = "La sede alcanzó su capacidad"

# Pedidos que ocupan a la cocina: aún no han salido de la sede.
ESTADOS_EN_CURSO = (EstadoPedido.RECIBIDO, EstadoPedido.EN_PREPARACION)


@dataclass(frozen=True)
class CapacidadSede:
    tope: int | None  # None = la sede no tiene tope configurado
    en_curso: int
    origen: str  # "franja", "general" o "sin_tope"

    @property
    def llena(self):
        return self.tope is not None and self.en_curso >= self.tope

    @property
    def disponibles(self):
        return None if self.tope is None else max(self.tope - self.en_curso, 0)


def franja_vigente(sede, momento):
    """Franja de capacidad activa que cubre el momento; si se solapan, la más estricta."""
    from apps.cobertura.models import CapacidadFranja

    hora = momento.time()
    return (
        CapacidadFranja.objects.filter(
            sede=sede,
            activa=True,
            dia_semana=momento.isoweekday(),
            hora_inicio__lte=hora,
            hora_fin__gt=hora,
        )
        .order_by("max_pedidos_simultaneos")
        .first()
    )


def _rango(fecha, desde, hasta):
    zona = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(fecha, desde), zona),
        timezone.make_aware(datetime.combine(fecha, hasta), zona),
    )


def verificar_capacidad_sede(sede, fecha_hora=None):
    """Compara los pedidos en curso de la franja actual con el tope vigente.

    - Con franja vigente: cuenta los pedidos Recibidos o En preparación creados
      dentro de esa franja hoy y los compara con `max_pedidos_simultaneos`.
    - Sin franja, con `tope_general_pedidos`: cuenta los en curso del día.
    - Sin ninguno: no hay tope y la sede nunca está llena.
    """
    momento = timezone.localtime(fecha_hora)
    fecha = momento.date()
    en_curso = Pedido.objects.filter(sede=sede, estado__in=ESTADOS_EN_CURSO)

    franja = franja_vigente(sede, momento)
    if franja is not None:
        inicio, fin = _rango(fecha, franja.hora_inicio, franja.hora_fin)
        return CapacidadSede(
            tope=franja.max_pedidos_simultaneos,
            en_curso=en_curso.filter(creado_en__gte=inicio, creado_en__lt=fin).count(),
            origen="franja",
        )

    if sede.tope_general_pedidos:
        inicio, fin = _rango(fecha, time.min, time.max)
        return CapacidadSede(
            tope=sede.tope_general_pedidos,
            en_curso=en_curso.filter(creado_en__gte=inicio, creado_en__lte=fin).count(),
            origen="general",
        )

    return CapacidadSede(tope=None, en_curso=en_curso.count(), origen="sin_tope")
