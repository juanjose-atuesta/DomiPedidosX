from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import (
    CanalNotificacion,
    ConfiguracionCorreos,
    EstadoEnvio,
    Notificacion,
    TipoNotificacion,
)

# Correo interno de los clientes registrados sin correo (ver usuarios.services).
DOMINIO_SIN_CORREO = "@sin-correo.invalid"

EVENTOS_CORREO = ("confirmacion", "cambio_estado", "cancelacion", "asignacion_repartidor")

TIPO_POR_EVENTO = {
    "confirmacion": TipoNotificacion.PEDIDO_CONFIRMADO,
    "cambio_estado": TipoNotificacion.CAMBIO_ESTADO,
    "cancelacion": TipoNotificacion.PEDIDO_CANCELADO,
    "asignacion_repartidor": TipoNotificacion.REPARTIDOR_ASIGNADO,
}


def crear_alerta_stock_bajo(
    *,
    sede,
    producto,
    stock_actual,
    stock_minimo,
):
    """Registra una alerta de panel cuando un producto llega al stock minimo."""
    mensaje = (
        f"El producto {producto.nombre} de la sede {sede.nombre} tiene "
        f"{stock_actual} unidades disponibles y su stock minimo es "
        f"{stock_minimo}. Es necesario reabastecer."
    )

    return Notificacion.objects.create(
        sede=sede,
        tipo=TipoNotificacion.ALERTA_STOCK_BAJO,
        canal=CanalNotificacion.SISTEMA,
        asunto=f"Stock bajo: {producto.nombre}",
        mensaje=mensaje,
    )


def crear_alerta_sin_repartidor(pedido):
    """Alerta de panel: la asignación automática no encontró repartidor libre."""
    ya_existe = Notificacion.objects.filter(
        pedido=pedido, tipo=TipoNotificacion.SIN_REPARTIDOR, leida=False
    ).exists()
    if ya_existe:
        return None
    return Notificacion.objects.create(
        sede=pedido.sede,
        pedido=pedido,
        tipo=TipoNotificacion.SIN_REPARTIDOR,
        canal=CanalNotificacion.SISTEMA,
        asunto=f"Pedido #{pedido.pk} sin repartidor",
        mensaje=(
            f"El pedido #{pedido.pk} está listo para despacho pero no hay "
            f"repartidores disponibles en {pedido.sede.nombre}. Se asignará "
            "cuando uno se libere, o puedes asignarlo manualmente."
        ),
    )


def notificar_cancelacion_a_sede(pedido):
    """Alerta de panel para el operador: el cliente canceló su pedido (HU-7.5).

    Va dirigida a la sede (sin usuario), así la ve cualquier operador de ella.
    Incluye el número de pedido y la hora exacta de la cancelación.
    """
    cancelado_en = timezone.localtime(pedido.actualizado_en or timezone.now())
    return Notificacion.objects.create(
        sede=pedido.sede,
        pedido=pedido,
        tipo=TipoNotificacion.PEDIDO_CANCELADO,
        canal=CanalNotificacion.SISTEMA,
        asunto=f"Pedido #{pedido.pk} cancelado por el cliente",
        mensaje=(
            f"El cliente canceló el pedido #{pedido.pk} de {pedido.sede.nombre} "
            f"a las {cancelado_en:%H:%M:%S} del {cancelado_en:%d/%m/%Y}. "
            f"Motivo: {pedido.motivo_cancelacion}"
        ),
    )


def notificar_repartidor_asignado(pedido):
    """Aviso de panel al repartidor al que se asigna un pedido (HU-7.6).

    Va dirigido al repartidor (usuario) e incluye número de pedido y dirección
    de entrega. Se crea en la misma transacción de la asignación, así aparece
    de inmediato (criterio: máximo 5 segundos) y, si la asignación se revierte,
    no queda ningún aviso.
    """
    return Notificacion.objects.create(
        usuario=pedido.repartidor,
        sede=pedido.sede,
        pedido=pedido,
        tipo=TipoNotificacion.REPARTIDOR_ASIGNADO,
        canal=CanalNotificacion.SISTEMA,
        asunto=f"Nuevo pedido #{pedido.pk}",
        mensaje=(
            f"Se te asignó el pedido #{pedido.pk}. "
            f"Dirección de entrega: {pedido.direccion_entrega}"
        ),
    )

def notificaciones_visibles_para(usuario):
    """Alertas de panel que ve el personal: las de sus sedes y las suyas propias.

    El admin ve las de todas las sedes de su negocio; operador y cocina ven las de sus sedes 
    y las suyas; el repartidor solo las suyas.
    """
    from django.db.models import Q

    from apps.sedes.models import Sede, SedeUsuario
    from apps.usuarios.models import Rol

    if usuario.rol == Rol.REPARTIDOR:
        # El repartidor solo ve los avisos dirigidos a él (HU-7.6), nunca las
        # alertas generales de la sede, que son del operador.
        return Notificacion.objects.filter(
            canal=CanalNotificacion.SISTEMA, usuario=usuario
        )

    if usuario.rol == Rol.ADMIN:
        sedes = Sede.objects.filter(negocio_id=usuario.negocio_id).values("pk")
    else:
        sedes = SedeUsuario.objects.filter(
            usuario=usuario, sede__negocio_id=usuario.negocio_id
        ).values("sede")
    return Notificacion.objects.filter(canal=CanalNotificacion.SISTEMA).filter(
        Q(usuario=usuario) | Q(usuario__isnull=True, sede__in=sedes)
    )


def configuracion_correos(negocio_id):
    """Configuración del negocio; sin fila, todos los eventos están activos."""
    return ConfiguracionCorreos.objects.filter(negocio_id=negocio_id).first() or (
        ConfiguracionCorreos(negocio_id=negocio_id)
    )


def correo_evento_activo(negocio_id, evento):
    if evento not in EVENTOS_CORREO:
        raise ValueError(f"Evento de correo desconocido: {evento}")
    return getattr(configuracion_correos(negocio_id), evento)


def notificar_cliente(pedido, evento, *, asunto, mensaje):
    """Envía un correo al cliente del pedido si el negocio tiene el evento activo.

    El envío ocurre al confirmar la transacción: si el cambio se revierte, no
    sale ningún correo. Cada envío queda registrado en Notificacion.
    Devuelve False si el correo no corresponde (sin cliente, sin correo real o
    evento desactivado).
    """
    cliente = pedido.cliente
    if cliente is None or not cliente.email or cliente.email.endswith(DOMINIO_SIN_CORREO):
        return False
    if not correo_evento_activo(pedido.sede.negocio_id, evento):
        return False

    def enviar():
        registro = Notificacion.objects.create(
            usuario=cliente,
            sede=pedido.sede,
            pedido=pedido,
            tipo=TIPO_POR_EVENTO[evento],
            canal=CanalNotificacion.CORREO,
            asunto=asunto,
            mensaje=mensaje,
            intentos=1,
        )
        try:
            send_mail(asunto, mensaje, None, [cliente.email], fail_silently=False)
        except Exception:  # el pedido no debe fallar porque el correo falle
            registro.estado_envio = EstadoEnvio.FALLIDO
        else:
            registro.estado_envio = EstadoEnvio.ENVIADO
            registro.enviado_en = timezone.now()
        registro.save(update_fields=["estado_envio", "enviado_en"])

    transaction.on_commit(enviar)
    return True


def _encabezado(pedido):
    return f"Hola {pedido.cliente_nombre},\n\n"


def notificar_confirmacion(pedido):
    from apps.promociones.services import formatear_pesos

    return notificar_cliente(
        pedido,
        "confirmacion",
        asunto=f"Recibimos tu pedido #{pedido.pk} - {pedido.sede.negocio.nombre}",
        mensaje=(
            _encabezado(pedido)
            + f"{pedido.sede.nombre} recibió tu pedido #{pedido.pk} por "
            + f"{formatear_pesos(pedido.total)}.\nTe avisaremos cuando cambie de estado."
        ),
    )


def notificar_cambio_estado(pedido):
    return notificar_cliente(
        pedido,
        "cambio_estado",
        asunto=f"Tu pedido #{pedido.pk}: {pedido.get_estado_display()}",
        mensaje=(
            _encabezado(pedido)
            + f"Tu pedido #{pedido.pk} ahora está: {pedido.get_estado_display()}."
        ),
    )


def notificar_cancelacion(pedido, *, por_sede):
    quien = "La sede rechazó" if por_sede else "Cancelaste"
    return notificar_cliente(
        pedido,
        "cancelacion",
        asunto=f"Pedido #{pedido.pk} cancelado",
        mensaje=(
            _encabezado(pedido)
            + f"{quien} el pedido #{pedido.pk}.\nMotivo: {pedido.motivo_cancelacion}"
        ),
    )


def notificar_asignacion(pedido):
    repartidor = pedido.repartidor
    return notificar_cliente(
        pedido,
        "asignacion_repartidor",
        asunto=f"Tu pedido #{pedido.pk} ya tiene repartidor",
        mensaje=(
            _encabezado(pedido)
            + f"{repartidor.nombre} llevará tu pedido #{pedido.pk}."
        ),
    )
