from django.db import transaction


def porcentaje_alerta_de_sede(sede):
    """Porcentaje de alerta de capacidad vigente para una sede (HU-9.3).

    Lo define el negocio y vale igual para todas sus sedes.
    """
    return sede.negocio.porcentaje_alerta_capacidad


def actualizar_porcentaje_alerta(negocio, porcentaje):
    """Guarda el porcentaje del negocio y lo aplica de inmediato a todas sus sedes.

    Las franjas de capacidad ya configuradas toman el nuevo umbral, así la
    alerta de cualquier sede usa el valor recién guardado.
    """
    from apps.cobertura.models import CapacidadFranja

    with transaction.atomic():
        negocio.porcentaje_alerta_capacidad = porcentaje
        negocio.save(update_fields=["porcentaje_alerta_capacidad", "actualizado_en"])
        CapacidadFranja.objects.filter(sede__negocio=negocio).update(
            umbral_alerta_pct=porcentaje
        )
    return negocio
