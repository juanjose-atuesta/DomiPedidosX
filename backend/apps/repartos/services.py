"""Asignación de repartidores a domicilios (HU-6.5 y HU-6.6).

`PerfilRepartidor.disponible` indica si el repartidor está libre. Queda
ocupado al recibir un pedido (manual, automático o tomándolo él mismo) y se
libera cuando ya no lleva ningún domicilio en curso.
"""

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.notificaciones.services import (
    crear_alerta_sin_repartidor,
    notificar_asignacion,
    notificar_repartidor_asignado,
)
from apps.pedidos.models import EstadoPedido, HistorialEstado, Pedido, TipoPedido
from apps.usuarios.models import PerfilRepartidor, Rol, User

ESTADOS_EN_CURSO = (EstadoPedido.LISTO_DESPACHO, EstadoPedido.EN_CAMINO)


def repartidores_de_sede(sede, *, hoy=None):
    """Repartidores activos asignados a la sede, con su carga del día.

    `pedidos_hoy`: pedidos de hoy (no cancelados) que tiene o tuvo asignados.
    `pedidos_en_curso`: domicilios que lleva ahora (listo o en camino).
    """
    hoy = hoy or timezone.localdate()
    return (
        User.objects.filter(
            rol=Rol.REPARTIDOR,
            is_active=True,
            sedes_asignadas__sede=sede,
        )
        .select_related("perfil_repartidor")
        .annotate(
            pedidos_hoy=Count(
                "entregas",
                filter=Q(entregas__creado_en__date=hoy)
                & ~Q(entregas__estado=EstadoPedido.CANCELADO),
                distinct=True,
            ),
            pedidos_en_curso=Count(
                "entregas",
                filter=Q(entregas__estado__in=ESTADOS_EN_CURSO),
                distinct=True,
            ),
        )
        .order_by("nombre", "apellido")
    )


def _perfil(usuario, *, bloquear=False):
    consulta = PerfilRepartidor.objects
    if bloquear:
        consulta = consulta.select_for_update()
    perfil, _ = consulta.get_or_create(usuario=usuario)
    return perfil


def esta_disponible(usuario):
    perfil = getattr(usuario, "perfil_repartidor", None)
    return perfil.disponible if perfil is not None else True


def marcar_ocupado(usuario):
    PerfilRepartidor.objects.update_or_create(
        usuario=usuario, defaults={"disponible": False}
    )


def liberar_si_corresponde(usuario):
    """Vuelve a disponible si ya no lleva domicilios en curso. Devuelve True si quedó libre."""
    if Pedido.objects.filter(repartidor=usuario, estado__in=ESTADOS_EN_CURSO).exists():
        return False
    PerfilRepartidor.objects.update_or_create(
        usuario=usuario, defaults={"disponible": True}
    )
    return True


def _validar_asignable(pedido):
    if pedido.tipo != TipoPedido.DOMICILIO:
        raise ValueError("Solo los pedidos a domicilio llevan repartidor.")
    if pedido.estado != EstadoPedido.LISTO_DESPACHO:
        raise ValueError(
            "Solo se asigna repartidor a pedidos en estado Listo para despacho."
        )


def _registrar_asignacion(pedido, repartidor, *, asignado_por, automatico):
    anterior = pedido.repartidor
    pedido.repartidor = repartidor
    pedido.save(update_fields=["repartidor", "actualizado_en"])
    marcar_ocupado(repartidor)
    if anterior is not None and anterior.pk != repartidor.pk:
        liberar_si_corresponde(anterior)

    modo = "automáticamente" if automatico else "manualmente"
    HistorialEstado.objects.create(
        pedido=pedido,
        estado=pedido.estado,
        cambiado_por=asignado_por,
        comentario=f"Repartidor {repartidor.nombre_completo} asignado {modo}.",
    )
    notificar_asignacion(pedido)
    notificar_repartidor_asignado(pedido)    # aviso al repartidor (HU-7.6)
    return pedido


def asignar_repartidor(pedido_id, repartidor_id, *, asignado_por):
    """Asignación manual por el operador (HU-6.5).

    El repartidor debe estar activo, trabajar en la sede del pedido y estar
    disponible. Reasignar libera al repartidor anterior.
    """
    with transaction.atomic():
        pedido = (
            Pedido.objects.select_for_update()
            .select_related("sede", "repartidor")
            .get(pk=pedido_id)
        )
        _validar_asignable(pedido)

        repartidor = repartidores_de_sede(pedido.sede).filter(pk=repartidor_id).first()
        if repartidor is None:
            raise ValueError("El repartidor no existe o no trabaja en esta sede.")
        if pedido.repartidor_id == repartidor.pk:
            return pedido

        perfil = _perfil(repartidor, bloquear=True)
        if not perfil.disponible:
            raise ValueError(
                f"{repartidor.nombre_completo} está ocupado con otra entrega."
            )
        return _registrar_asignacion(
            pedido, repartidor, asignado_por=asignado_por, automatico=False
        )


def elegir_repartidor(sede):
    """El repartidor disponible de la sede con menos pedidos hoy (HU-6.6)."""
    candidatos = (
        repartidores_de_sede(sede)
        .filter(Q(perfil_repartidor__disponible=True) | Q(perfil_repartidor__isnull=True))
        .order_by("pedidos_hoy", "nombre", "apellido", "id")
    )
    return candidatos.first()


def asignar_automaticamente(pedido):
    """Asigna el pedido si hay alguien libre; si no, deja una alerta al operador.

    Debe llamarse dentro de una transacción con el pedido bloqueado.
    Devuelve el repartidor asignado o None.
    """
    _validar_asignable(pedido)
    if pedido.repartidor_id:
        return pedido.repartidor
    repartidor = elegir_repartidor(pedido.sede)
    if repartidor is None:
        crear_alerta_sin_repartidor(pedido)
        return None
    _perfil(repartidor, bloquear=True)
    _registrar_asignacion(pedido, repartidor, asignado_por=None, automatico=True)
    return repartidor


def asignar_pendientes(sede):
    """Reparte los domicilios que esperaban repartidor, del más antiguo al más nuevo."""
    if not sede.asignacion_automatica_repartidor:
        return
    pendientes = (
        Pedido.objects.select_for_update()
        .select_related("sede__negocio")
        .filter(
            sede=sede,
            tipo=TipoPedido.DOMICILIO,
            estado=EstadoPedido.LISTO_DESPACHO,
            repartidor__isnull=True,
        )
        .order_by("creado_en")
    )
    for pedido in pendientes:
        if asignar_automaticamente(pedido) is None:
            break
