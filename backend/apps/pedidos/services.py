from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.cobertura.services import zona_para_entrega
from apps.inventario.models import InventarioSede
from apps.menu.models import (
    OpcionProducto,
    Producto,
    ProductoCombo,
    TipoGrupoOpcion,
)
from apps.notificaciones.services import crear_alerta_stock_bajo
from apps.promociones.services import (
    buscar_promocion,
    calcular_descuento_promocion,
    formatear_pesos,
)
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
            producto__negocio_id=sede.negocio_id,
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
    """Pedidos visibles: el cliente los suyos, el admin los de su negocio y el
    resto los de sus sedes."""
    if usuario.rol == Rol.CLIENTE:
        return Pedido.objects.filter(cliente=usuario)
    if usuario.rol == Rol.ADMIN:
        return Pedido.objects.filter(sede__negocio_id=usuario.negocio_id)
    pedidos = Pedido.objects.filter(
        sede__in=SedeUsuario.objects.filter(usuario=usuario).values("sede")
    )
    if usuario.rol == Rol.REPARTIDOR:
        # Solo domicilios: los que ya lleva y los despachables que nadie ha tomado.
        return pedidos.filter(tipo=TipoPedido.DOMICILIO).filter(
            Q(repartidor=usuario)
            | Q(
                repartidor__isnull=True,
                estado__in=[EstadoPedido.LISTO_DESPACHO, EstadoPedido.EN_CAMINO],
            )
        )
    return pedidos


def cambiar_estado_pedido(pedido_id, *, estado, usuario, comentario=""):
    """Avanza el estado de un pedido y lo registra en el historial."""
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
        campos = ["estado", "actualizado_en"]

        if usuario.rol == Rol.REPARTIDOR:
            # Bajo el bloqueo: si dos lo toman a la vez, el segundo se rechaza aquí.
            if pedido.repartidor_id not in (None, usuario.pk):
                raise ValueError("Este pedido ya lo tomó otro repartidor.")
            pedido.repartidor = usuario
            campos.append("repartidor")

        if estado not in estados_siguientes(pedido):
            raise ValueError(
                f"Un pedido en estado {pedido.get_estado_display()} no puede "
                f"pasar a {EstadoPedido(estado).label}."
            )

        pedido.estado = estado
        pedido.save(update_fields=campos)
        HistorialEstado.objects.create(
            pedido=pedido,
            estado=estado,
            cambiado_por=usuario,
            comentario=comentario,
        )
        return pedido


MENSAJE_FUERA_DE_COBERTURA = "Tu dirección está fuera de la zona de cobertura"


def sede_abierta(sede, momento=None):
    """La sede atiende en este momento según su horario del día."""
    momento = timezone.localtime(momento)
    hora = momento.time()
    return sede.horarios.filter(
        dia_semana=momento.isoweekday(),
        hora_apertura__lte=hora,
        hora_cierre__gt=hora,
    ).exists()


def _mensaje_sede_cerrada(sede, momento=None):
    momento = timezone.localtime(momento)
    tramos = [
        f"{h.hora_apertura:%H:%M} a {h.hora_cierre:%H:%M}"
        for h in sede.horarios.filter(dia_semana=momento.isoweekday()).order_by(
            "hora_apertura"
        )
    ]
    if not tramos:
        return f"La sede {sede.nombre} no atiende hoy."
    return (
        f"La sede {sede.nombre} está cerrada en este momento. "
        f"Hoy atiende de {' y de '.join(tramos)}."
    )


def _calcular_lineas(detalles):
    lineas = []
    subtotal = Decimal("0.00")
    por_producto = defaultdict(lambda: Decimal("0.00"))

    for detalle in detalles:
        producto = detalle["producto"]
        adicionales = sum(
            (opcion.precio_adicional for opcion in detalle["opciones"]),
            Decimal("0.00"),
        )
        subtotal_linea = (producto.precio_base + adicionales) * detalle["cantidad"]
        subtotal += subtotal_linea
        por_producto[producto.pk] += subtotal_linea
        lineas.append(
            {
                **detalle,
                "precio_unitario": producto.precio_base,
                "subtotal": subtotal_linea,
            }
        )
    return lineas, subtotal, por_producto


def _cotizar(
    *,
    sede,
    detalles,
    tipo,
    entrega_lat,
    entrega_lng,
    codigo_promocion,
    promocion_id,
    bloquear_promocion=False,
):
    """Calcula el pedido en el servidor y reúne los motivos que impiden confirmarlo.

    `detalles` ya viene normalizado y validado para la sede. Nada del total
    (domicilio, descuento) se toma de lo que envía el cliente.
    """
    lineas, subtotal, por_producto = _calcular_lineas(detalles)
    problemas = []
    momento = timezone.now()

    if not sede_abierta(sede, momento):
        problemas.append(_mensaje_sede_cerrada(sede, momento))

    zona = None
    costo_domicilio = Decimal("0.00")
    if tipo == TipoPedido.DOMICILIO:
        if entrega_lat is not None and entrega_lng is not None:
            zona = zona_para_entrega(sede, entrega_lat, entrega_lng)
        if zona is None:
            problemas.append(MENSAJE_FUERA_DE_COBERTURA)
        else:
            costo_domicilio = zona.tarifa_domicilio
            if subtotal < zona.pedido_minimo:
                problemas.append(
                    f"El pedido mínimo para tu zona ({zona.nombre}) es "
                    f"{formatear_pesos(zona.pedido_minimo)}. Te faltan "
                    f"{formatear_pesos(zona.pedido_minimo - subtotal)}."
                )

    promocion = None
    descuento = Decimal("0.00")
    error_promocion = ""
    if codigo_promocion or promocion_id:
        promocion = buscar_promocion(
            negocio_id=sede.negocio_id,
            codigo=codigo_promocion,
            promocion_id=promocion_id,
            bloquear=bloquear_promocion,
        )
        if promocion is None:
            error_promocion = "El código de promoción no existe."
        else:
            try:
                descuento = calcular_descuento_promocion(
                    promocion,
                    sede=sede,
                    subtotal=subtotal,
                    subtotales_por_producto=por_producto,
                )
            except ValueError as exc:
                error_promocion = str(exc)
        if error_promocion:
            promocion = None
            descuento = Decimal("0.00")
            problemas.append(error_promocion)

    if tipo == TipoPedido.DOMICILIO and zona is not None:
        minutos = zona.tiempo_estimado_min
    else:
        minutos = max(
            (d["producto"].tiempo_preparacion_min for d in detalles), default=0
        )

    return {
        "lineas": lineas,
        "subtotal": subtotal,
        "descuento": descuento,
        "costo_domicilio": costo_domicilio,
        "total": subtotal + costo_domicilio - descuento,
        "zona": zona,
        "promocion": promocion,
        "error_promocion": error_promocion,
        "tiempo_estimado_entrega": momento + timedelta(minutes=minutos),
        "tiempo_estimado_min": minutos,
        "problemas": problemas,
    }


def _preparar(sede, sede_id, detalles, tipo):
    sede = _resolver_sede(sede=sede, sede_id=sede_id)
    detalles = _normalizar_detalles(detalles)
    _validar_venta_en_sede(sede, detalles)
    if tipo not in TipoPedido.values:
        raise ValueError("El tipo de pedido no es valido.")
    return sede, detalles


def cotizar_pedido(
    *,
    detalles,
    sede=None,
    sede_id=None,
    tipo=TipoPedido.RECOGER,
    entrega_lat=None,
    entrega_lng=None,
    codigo_promocion="",
    promocion_id=None,
):
    """Desglose del pedido sin guardarlo: lo usa el carrito antes de confirmar."""
    sede, detalles = _preparar(sede, sede_id, detalles, tipo)
    return _cotizar(
        sede=sede,
        detalles=detalles,
        tipo=tipo,
        entrega_lat=entrega_lat,
        entrega_lng=entrega_lng,
        codigo_promocion=codigo_promocion,
        promocion_id=promocion_id,
    )


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
    codigo_promocion="",
    promocion_id=None,
    observaciones="",
):
    """Registra y confirma un pedido, descontando el inventario de su sede.

    Valida en el servidor que la sede esté abierta, que la dirección esté en
    una zona de cobertura y alcance su pedido mínimo, y la promoción. El
    costo de domicilio y el descuento se calculan aquí, nunca se reciben.
    """
    with transaction.atomic():
        sede, detalles = _preparar(sede, sede_id, detalles, tipo)

        if canal not in CanalPedido.values:
            raise ValueError("El canal del pedido no es valido.")
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

        cotizacion = _cotizar(
            sede=sede,
            detalles=detalles,
            tipo=tipo,
            entrega_lat=entrega_lat,
            entrega_lng=entrega_lng,
            codigo_promocion=codigo_promocion,
            promocion_id=promocion_id,
            bloquear_promocion=True,
        )
        if cotizacion["problemas"]:
            raise ValueError(cotizacion["problemas"][0])

        if not cliente_nombre and cliente is not None:
            cliente_nombre = getattr(cliente, "nombre_completo", "") or ""
        if not cliente_telefono and cliente is not None:
            cliente_telefono = getattr(cliente, "telefono", "") or ""
        cliente_nombre = cliente_nombre or "Cliente"
        cliente_telefono = cliente_telefono or ""

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
            zona=cotizacion["zona"],
            promocion=cotizacion["promocion"],
            estado=EstadoPedido.RECIBIDO,
            metodo_pago=metodo_pago,
            subtotal=cotizacion["subtotal"],
            costo_domicilio=cotizacion["costo_domicilio"],
            descuento=cotizacion["descuento"],
            total=cotizacion["total"],
            tiempo_estimado_entrega=cotizacion["tiempo_estimado_entrega"],
            observaciones=observaciones or "",
        )

        for linea in cotizacion["lineas"]:
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


def _requerimientos_de_stock(pedido):
    """Unidades por producto base (los combos se expanden en sus componentes)."""
    requerimientos = defaultdict(int)
    cache_componentes = {}
    for detalle in pedido.detalles.select_related("producto").all():
        _expandir_producto(
            detalle.producto,
            detalle.cantidad,
            requerimientos,
            cache=cache_componentes,
        )
    return requerimientos


def cancelar_pedido(pedido_id, *, usuario, motivo=""):
    """El cliente cancela su pedido mientras sigue en estado Recibido (HU-5.6).

    Devuelve al inventario de la sede lo que se descontó al confirmarlo y
    deja la cancelación en el historial. El cupo de la promoción se libera
    solo porque los pedidos cancelados no cuentan.
    """
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
        if pedido.estado != EstadoPedido.RECIBIDO:
            raise ValueError(
                "Solo puedes cancelar un pedido mientras está en estado "
                f"Recibido. Este pedido está {pedido.get_estado_display()}."
            )

        motivo = (motivo or "").strip() or "Cancelado por el cliente."
        pedido.estado = EstadoPedido.CANCELADO
        pedido.motivo_cancelacion = motivo
        pedido.save(update_fields=["estado", "motivo_cancelacion", "actualizado_en"])

        reponer_stock_pedido(pedido)
        HistorialEstado.objects.create(
            pedido=pedido,
            estado=EstadoPedido.CANCELADO,
            cambiado_por=usuario,
            comentario=motivo,
        )
        return pedido


def reponer_stock_pedido(pedido):
    """Devuelve al inventario de la sede las unidades del pedido."""
    requerimientos = _requerimientos_de_stock(pedido)
    inventarios = (
        InventarioSede.objects.select_for_update()
        .filter(
            sede_id=pedido.sede_id,
            producto_id__in=list(requerimientos),
            controla_stock=True,
        )
        .order_by("producto_id")
    )
    for inventario in inventarios:
        inventario.stock_actual += requerimientos[inventario.producto_id]
        inventario.save(update_fields=["stock_actual"])


def descontar_stock_pedido(pedido):
    """Descuenta el inventario de todos los productos de un pedido."""
    with transaction.atomic():
        if pedido.pk is None:
            raise ValueError("El pedido debe estar guardado antes de descontar stock.")

        requerimientos = _requerimientos_de_stock(pedido)

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
