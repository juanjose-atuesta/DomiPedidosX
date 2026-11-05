from .models import CanalNotificacion, Notificacion, TipoNotificacion


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
