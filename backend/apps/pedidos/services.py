from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import serializers

from apps.inventario.models import InventarioSede
from apps.menu.models import (
    OpcionProducto,
    Producto,
    ProductoCombo,
    TipoGrupoOpcion,
)
from apps.notificaciones.services import crear_alerta_stock_bajo
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol

from .models import (
    CanalPedido,
    DetallePedido,
    DetallePedidoOpcion,
    EstadoPedido,
    HistorialEstado,
    MetodoPago,
    Pedido,
    TipoPedido,
)


def _decimal_no_negativo(valor, campo):
    try:
        valor = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un numero valido.")

    if valor < 0:
        raise ValueError(f"{campo} no puede ser negativo.")

    return valor


def _entero_positivo(valor, campo):
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un numero entero valido.")

    if valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")

    return valor


def _resolver_sede(sede=None, sede_id=None):
    if not isinstance(sede, Sede):
        if sede is None:
            sede = sede_id

        try:
            sede = Sede.objects.get(pk=sede)
        except (Sede.DoesNotExist, ValueError, TypeError):
            raise ValueError("La sede indicada no existe.")

    if not sede.activa:
        raise ValueError("La sede indicada no esta activa.")

    return sede


def _resolver_producto(valor):
    if isinstance(valor, Producto):
        return valor

    try:
        return Producto.objects.get(pk=valor)
    except (Producto.DoesNotExist, ValueError, TypeError):
        raise ValueError("El producto indicado no existe.")


def _resolver_opcion(valor):
    if isinstance(valor, OpcionProducto):
        return valor

    if isinstance(valor, dict):
        valor = (
            valor.get("opcion")
            or valor.get("opcion_id")
            or valor.get("id")
        )

    try:
        return OpcionProducto.objects.select_related("grupo").get(pk=valor)
    except (OpcionProducto.DoesNotExist, ValueError, TypeError):
        raise ValueError("La opcion indicada no existe.")


def _expandir_producto(
    producto,
    cantidad,
    requerimientos,
    *,
    ruta=None,
    cache=None,
):
    ruta = set() if ruta is None else ruta
    cache = {} if cache is None else cache

    if not producto.es_combo:
        requerimientos[producto.pk] += cantidad
        return

    if producto.pk in ruta:
        raise ValueError("El combo contiene un ciclo en sus componentes.")

    if producto.pk not in cache:
        cache[producto.pk] = list(
            ProductoCombo.objects.filter(combo=producto).select_related(
                "producto"
            )
        )

    siguiente_ruta = ruta | {producto.pk}
    for componente in cache[producto.pk]:
        _expandir_producto(
            componente.producto,
            cantidad * componente.cantidad,
            requerimientos,
            ruta=siguiente_ruta,
            cache=cache,
        )


def _normalizar_detalles(detalles):
    if not detalles:
        raise ValueError("El pedido debe incluir al menos un producto.")

    normalizados = []

    for item in detalles:
        if not isinstance(item, dict):
            raise ValueError("Cada detalle del pedido debe ser un objeto.")

        producto = item.get("producto")
        if producto is None:
            producto = item.get("producto_id")
        producto = _resolver_producto(producto)

        if not producto.disponible:
            raise ValueError(
                f"El producto {producto.nombre} no esta disponible."
            )

        cantidad = _entero_positivo(
            item.get("cantidad"), "cantidad del producto"
        )
        notas_producto = item.get("notas_producto") or ""

        opciones_ingresadas = item.get("opciones") or []
        if not isinstance(opciones_ingresadas, (list, tuple)):
            raise ValueError("Las opciones del producto deben ser una lista.")

        opciones = []
        for opcion_ingresada in opciones_ingresadas:
            opcion = _resolver_opcion(opcion_ingresada)
            if opcion.grupo.producto_id != producto.pk:
                raise ValueError(
                    f"La opcion {opcion.nombre} no pertenece al producto "
                    f"{producto.nombre}."
                )
            if not opcion.activa:
                raise ValueError(
                    f"La opcion {opcion.nombre} no esta activa."
                )
            opciones.append(opcion)

        normalizados.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "notas_producto": notas_producto,
                "opciones": opciones,
            }
        )

    return normalizados


def _nombre_opcion_en_pedido(opcion):
    """Un ingrediente excluible se guarda como 'Sin x' para que cocina lo lea bien."""
    nombre = opcion.nombre
    if opcion.grupo.tipo != TipoGrupoOpcion.EXCLUIBLE:
        return nombre
    if nombre.lower().startswith("sin "):
        return nombre
    return f"Sin {nombre.lower()}"


def _validar_venta_en_sede(sede, detalles):
    """Sin fila de inventario disponible, el producto no se vende en la sede."""
    vendibles = set(
        InventarioSede.objects.filter(
            sede=sede,
            disponible_en_sede=True,
            producto__in=[detalle["producto"] for detalle in detalles],
        ).values_list("producto_id", flat=True)
    )
    for detalle in detalles:
        if detalle["producto"].pk not in vendibles:
            raise ValueError(
                f"El producto {detalle['producto'].nombre} no se vende en "
                "esta sede."
            )


def estados_siguientes(pedido):
    """Estados a los que puede pasar un pedido según su estado y tipo."""
    if pedido.estado == EstadoPedido.RECIBIDO:
        return [EstadoPedido.EN_PREPARACION]
    if pedido.estado == EstadoPedido.EN_PREPARACION:
        return [EstadoPedido.LISTO_DESPACHO]
    if pedido.estado == EstadoPedido.LISTO_DESPACHO:
        if pedido.tipo == TipoPedido.DOMICILIO:
            return [EstadoPedido.EN_CAMINO]
        return [EstadoPedido.ENTREGADO]
    if pedido.estado == EstadoPedido.EN_CAMINO:
        return [EstadoPedido.ENTREGADO]
    return []


def pedidos_visibles_para(usuario):
    """Pedidos que puede consultar el usuario: el admin todos, el resto los de sus sedes."""
    if usuario.rol == Rol.ADMIN:
        return Pedido.objects.all()
    return Pedido.objects.filter(
        sede__in=SedeUsuario.objects.filter(usuario=usuario).values("sede")
    )


def cambiar_estado_pedido(pedido_id, *, estado, usuario, comentario=""):
    """Avanza el estado de un pedido y lo registra en el historial."""
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)

        if estado not in estados_siguientes(pedido):
            raise ValueError(
                f"Un pedido en estado {pedido.get_estado_display()} no puede "
                f"pasar a {EstadoPedido(estado).label}."
            )

        pedido.estado = estado
        pedido.save(update_fields=["estado", "actualizado_en"])
        HistorialEstado.objects.create(
            pedido=pedido,
            estado=estado,
            cambiado_por=usuario,
            comentario=comentario,
        )
        return pedido


def crear_pedido(
    *,
    detalles,
    sede=None,
    sede_id=None,
    cliente=None,
    creado_por=None,
    cliente_nombre="",
    cliente_telefono="",
    canal=CanalPedido.WEB,
    tipo=TipoPedido.RECOGER,
    metodo_pago=MetodoPago.EFECTIVO,
    direccion_entrega="",
    entrega_lat=None,
    entrega_lng=None,
    costo_domicilio=0,
    descuento=0,
    observaciones="",
):
    """Registra y confirma un pedido, descontando el inventario de su sede."""
    with transaction.atomic():
        sede = _resolver_sede(sede=sede, sede_id=sede_id)
        detalles = _normalizar_detalles(detalles)
        _validar_venta_en_sede(sede, detalles)

        if canal not in CanalPedido.values:
            raise ValueError("El canal del pedido no es valido.")
        if tipo not in TipoPedido.values:
            raise ValueError("El tipo de pedido no es valido.")
        if metodo_pago not in MetodoPago.values:
            raise ValueError("El metodo de pago no es valido.")

        if tipo == TipoPedido.DOMICILIO and (
            not direccion_entrega
            or entrega_lat is None
            or entrega_lng is None
        ):
            raise ValueError(
                "Los pedidos a domicilio requieren direccion_entrega, "
                "entrega_lat y entrega_lng."
            )

        costo_domicilio = _decimal_no_negativo(
            costo_domicilio, "costo_domicilio"
        )
        descuento = _decimal_no_negativo(descuento, "descuento")

        if not cliente_nombre and cliente is not None:
            cliente_nombre = getattr(cliente, "nombre_completo", "") or ""
        if not cliente_telefono and cliente is not None:
            cliente_telefono = getattr(cliente, "telefono", "") or ""
        cliente_nombre = cliente_nombre or "Cliente"
        cliente_telefono = cliente_telefono or ""

        subtotal = Decimal("0.00")
        lineas = []

        for detalle in detalles:
            producto = detalle["producto"]
            cantidad = detalle["cantidad"]
            opciones = detalle["opciones"]

            precio_unitario = producto.precio_base
            adicionales = sum(
                (opcion.precio_adicional for opcion in opciones),
                Decimal("0.00"),
            )
            subtotal_linea = (
                precio_unitario + adicionales
            ) * cantidad
            subtotal += subtotal_linea

            lineas.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "notas_producto": detalle["notas_producto"],
                    "opciones": opciones,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal_linea,
                }
            )

        total = subtotal + costo_domicilio - descuento
        if total < 0:
            raise ValueError(
                "El descuento no puede superar el subtotal mas el costo "
                "de domicilio."
            )

        pedido = Pedido.objects.create(
            cliente=cliente,
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            creado_por=creado_por,
            canal=canal,
            tipo=tipo,
            sede=sede,
            direccion_entrega=direccion_entrega or "",
            entrega_lat=entrega_lat,
            entrega_lng=entrega_lng,
            estado=EstadoPedido.RECIBIDO,
            metodo_pago=metodo_pago,
            subtotal=subtotal,
            costo_domicilio=costo_domicilio,
            descuento=descuento,
            total=total,
            observaciones=observaciones or "",
        )

        for linea in lineas:
            detalle_pedido = DetallePedido.objects.create(
                pedido=pedido,
                producto=linea["producto"],
                nombre_producto=linea["producto"].nombre,
                cantidad=linea["cantidad"],
                precio_unitario=linea["precio_unitario"],
                subtotal=linea["subtotal"],
                notas_producto=linea["notas_producto"],
            )
            DetallePedidoOpcion.objects.bulk_create(
                [
                    DetallePedidoOpcion(
                        detalle=detalle_pedido,
                        opcion=opcion,
                        nombre_opcion=_nombre_opcion_en_pedido(opcion),
                        precio_adicional=opcion.precio_adicional,
                    )
                    for opcion in linea["opciones"]
                ]
            )

        HistorialEstado.objects.create(
            pedido=pedido,
            estado=EstadoPedido.RECIBIDO,
            cambiado_por=creado_por,
            comentario="Pedido registrado y confirmado.",
        )

        descontar_stock_pedido(pedido)
        return pedido


def descontar_stock_pedido(pedido):
    """Descuenta el inventario de todos los productos de un pedido."""
    with transaction.atomic():
        if pedido.pk is None:
            raise ValueError("El pedido debe estar guardado antes de descontar stock.")

        requerimientos = defaultdict(int)
        cache_componentes = {}

        detalles = pedido.detalles.select_related("producto").all()
        for detalle in detalles:
            _expandir_producto(
                detalle.producto,
                detalle.cantidad,
                requerimientos,
                cache=cache_componentes,
            )

        inventarios = {
            inventario.producto_id: inventario
            for inventario in InventarioSede.objects.select_for_update()
            .select_related("producto")
            .filter(
                sede_id=pedido.sede_id,
                producto_id__in=list(requerimientos),
            )
            .order_by("producto_id")
        }

        for producto_id, cantidad_requerida in requerimientos.items():
            inventario = inventarios.get(producto_id)
            if inventario is None or not inventario.controla_stock:
                continue

            if inventario.stock_actual < cantidad_requerida:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Stock insuficiente para el producto "
                            f"{inventario.producto.nombre} en esta sede."
                        )
                    }
                )

        for producto_id, cantidad_requerida in requerimientos.items():
            inventario = inventarios.get(producto_id)
            if inventario is None or not inventario.controla_stock:
                continue

            inventario.stock_actual -= cantidad_requerida
            inventario.save(update_fields=["stock_actual"])

            if inventario.stock_actual <= inventario.stock_minimo:
                crear_alerta_stock_bajo(
                    sede=pedido.sede,
                    producto=inventario.producto,
                    stock_actual=inventario.stock_actual,
                    stock_minimo=inventario.stock_minimo,
                )

        return pedido
