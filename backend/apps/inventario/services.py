from django.db import transaction

from apps.menu.models import Producto
from apps.notificaciones.services import crear_alerta_stock_bajo
from apps.sedes.models import Sede

from .models import InventarioSede


def _obtener_sede_activa(sede_id):
    try:
        sede = Sede.objects.get(pk=sede_id)
    except (Sede.DoesNotExist, ValueError, TypeError):
        raise ValueError("La sede indicada no existe.")

    if not sede.activa:
        raise ValueError("La sede indicada no esta activa.")

    return sede


def _obtener_producto_disponible(producto_id, sede):
    try:
        # Un producto de otro negocio es como si no existiera.
        producto = Producto.objects.get(pk=producto_id, negocio_id=sede.negocio_id)
    except (Producto.DoesNotExist, ValueError, TypeError):
        raise ValueError("El producto indicado no existe.")

    if not producto.disponible:
        raise ValueError("El producto indicado no esta disponible.")

    return producto


def _entero_no_negativo(valor, campo):
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un numero entero valido.")

    if valor < 0:
        raise ValueError(f"{campo} no puede ser negativo.")

    return valor


def _booleano(valor, campo):
    if isinstance(valor, bool):
        return valor

    if isinstance(valor, str):
        normalizado = valor.strip().lower()
        if normalizado in ("true", "1", "si", "sí"):
            return True
        if normalizado in ("false", "0", "no"):
            return False

    raise ValueError(f"{campo} debe ser verdadero o falso.")


def asignar_o_actualizar_inventario_sede(
    *,
    sede_id,
    producto_id,
    disponible_en_sede=True,
    controla_stock=True,
    stock_actual=0,
    stock_minimo=5,
):
    with transaction.atomic():
        sede = _obtener_sede_activa(sede_id)
        producto = _obtener_producto_disponible(producto_id, sede)

        disponible_en_sede = _booleano(
            disponible_en_sede, "disponible_en_sede"
        )
        controla_stock = _booleano(controla_stock, "controla_stock")
        stock_actual = _entero_no_negativo(
            stock_actual, "stock_actual"
        )
        stock_minimo = _entero_no_negativo(
            stock_minimo, "stock_minimo"
        )

        inventario, creado = InventarioSede.objects.update_or_create(
            sede=sede,
            producto=producto,
            defaults={
                "disponible_en_sede": disponible_en_sede,
                "controla_stock": controla_stock,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
            },
        )

        if controla_stock and stock_actual <= stock_minimo:
            crear_alerta_stock_bajo(
                sede=sede,
                producto=producto,
                stock_actual=stock_actual,
                stock_minimo=stock_minimo,
            )

        inventario._fue_creado = creado
        return inventario


def cambiar_disponibilidad_producto_sede(
    *,
    sede_id,
    producto_id,
    disponible,
):
    with transaction.atomic():
        sede = _obtener_sede_activa(sede_id)
        producto = _obtener_producto_disponible(producto_id, sede)

        try:
            inventario = InventarioSede.objects.select_for_update().get(
                sede=sede,
                producto=producto,
            )
        except InventarioSede.DoesNotExist:
            raise ValueError(
                "El producto no esta registrado en el inventario de la sede."
            )

        inventario.disponible_en_sede = _booleano(
            disponible, "disponible"
        )
        inventario.save(update_fields=["disponible_en_sede"])
        return inventario


def descontar_stock_pedido(pedido):
    """Compatibilidad: el descuento vive en el flujo de pedidos."""
    from apps.pedidos.services import (
        descontar_stock_pedido as _descontar_stock_pedido,
    )

    return _descontar_stock_pedido(pedido)
