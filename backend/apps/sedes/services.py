from django.db import transaction

from .models import HorarioAtencion, Sede


def validar_horarios(horarios):
    """Valida coherencia y traslapes de una lista de horarios (dicts)."""
    if not horarios:
        return

    tramos_por_dia = {}
    for horario in horarios:
        dia = horario.get("dia_semana")
        apertura = horario.get("hora_apertura")
        cierre = horario.get("hora_cierre")

        if dia is None or not 1 <= int(dia) <= 7:
            raise ValueError("El día de la semana debe estar entre 1 y 7.")
        if apertura is None or cierre is None:
            raise ValueError(
                "Cada horario debe tener hora de apertura y de cierre."
            )
        if cierre <= apertura:
            raise ValueError(
                "La hora de cierre debe ser mayor que la hora de apertura."
            )

        tramos_por_dia.setdefault(int(dia), []).append((apertura, cierre))

    for tramos in tramos_por_dia.values():
        tramos.sort(key=lambda tramo: tramo[0])
        for anterior, siguiente in zip(tramos, tramos[1:]):
            if siguiente[0] < anterior[1]:
                raise ValueError(
                    "Los horarios de un mismo día no pueden traslaparse."
                )


def crear_sede(
    *,
    negocio,
    nombre,
    direccion,
    telefono=None,
    latitud=None,
    longitud=None,
    horarios=None,
):
    """Crea una sede y sus horarios de atención dentro de una transacción."""
    horarios = horarios or []
    validar_horarios(horarios)

    with transaction.atomic():
        sede = Sede.objects.create(
            negocio=negocio,
            nombre=nombre,
            direccion=direccion,
            telefono=telefono or "",
            latitud=latitud,
            longitud=longitud,
        )
        HorarioAtencion.objects.bulk_create(
            [
                HorarioAtencion(sede=sede, **horario)
                for horario in horarios
            ]
        )
        return sede


def actualizar_sede(sede, *, datos_sede, horarios=None):
    """Actualiza los datos de la sede y, si se envían, sus horarios."""
    with transaction.atomic():
        campos_actualizados = {}

        for campo in ("nombre", "direccion", "telefono", "latitud", "longitud"):
            if campo not in datos_sede:
                continue
            valor = datos_sede[campo]
            if campo == "telefono" and valor is None:
                valor = ""
            setattr(sede, campo, valor)
            campos_actualizados[campo] = valor

        if campos_actualizados:
            sede.save(update_fields=list(campos_actualizados))

        if horarios is not None:
            validar_horarios(horarios)
            sede.horarios.all().delete()
            HorarioAtencion.objects.bulk_create(
                [
                    HorarioAtencion(sede=sede, **horario)
                    for horario in horarios
                ]
            )

        return sede


def desactivar_sede(sede):
    """Aplica borrado lógico: la sede deja de estar activa, no se elimina."""
    with transaction.atomic():
        sede.activa = False
        sede.save(update_fields=["activa"])
        return sede


def reactivar_sede(sede):
    """Revierte el borrado lógico: la sede vuelve a estar activa."""
    with transaction.atomic():
        sede.activa = True
        sede.save(update_fields=["activa"])
        return sede
