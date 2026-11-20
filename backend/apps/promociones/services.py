from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.menu.models import Producto
from apps.sedes.models import Sede

from .models import Promocion, PromocionProducto


def _decimal(valor, campo, *, positivo=False):
    try:
        valor = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{campo} debe ser un numero valido.")

    if positivo and valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    if not positivo and valor < 0:
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


def _fecha(valor, campo):
    if isinstance(valor, date):
        return valor

    fecha = parse_date(str(valor))
    if fecha is None:
        raise ValueError(f"{campo} debe ser una fecha valida.")
    return fecha


def _resolver_sede(sede_id, negocio_id):
    if sede_id in (None, ""):
        return None

    try:
        return Sede.objects.get(pk=sede_id, negocio_id=negocio_id)
    except (Sede.DoesNotExist, ValueError, TypeError):
        raise ValueError("La sede indicada no existe.")


def _resolver_productos(productos_ids, negocio_id):
    productos = []
    productos_vistos = set()

    for valor in productos_ids or []:
        if isinstance(valor, Producto):
            producto = valor
        else:
            try:
                producto = Producto.objects.get(pk=valor, negocio_id=negocio_id)
            except (Producto.DoesNotExist, ValueError, TypeError):
                raise ValueError("Uno de los productos indicados no existe.")

        if producto.pk not in productos_vistos:
            productos_vistos.add(producto.pk)
            productos.append(producto)

    return productos


def _validar_descuento(porcentaje_descuento, monto_descuento):
    if porcentaje_descuento is not None and monto_descuento is not None:
        raise ValueError(
            "Debe indicar solo un tipo de descuento: porcentaje o monto."
        )

    if porcentaje_descuento is None and monto_descuento is None:
        raise ValueError(
            "Debe indicar un descuento por porcentaje o por monto."
        )

    if porcentaje_descuento is not None:
        porcentaje = _decimal(
            porcentaje_descuento, "porcentaje_descuento", positivo=True
        )
        if porcentaje > 100:
            raise ValueError(
                "porcentaje_descuento no puede ser mayor que 100."
            )
        return porcentaje, None

    monto = _decimal(monto_descuento, "monto_descuento", positivo=True)
    return None, monto


def _validar_fechas(fecha_inicio, fecha_fin):
    inicio = _fecha(fecha_inicio, "fecha_inicio")
    fin = _fecha(fecha_fin, "fecha_fin")

    if fin < inicio:
        raise ValueError("fecha_fin no puede ser anterior a fecha_inicio.")

    return inicio, fin


def _validar_cupo(cupo_maximo_diario):
    if cupo_maximo_diario is None:
        raise ValueError("cupo_maximo_diario es obligatorio.")
    return _entero_positivo(cupo_maximo_diario, "cupo_maximo_diario")


def _normalizar_codigo(codigo):
    if codigo is None:
        return None
    codigo = str(codigo).strip()
    return codigo or None


def _validar_codigo_unico(codigo, negocio_id, *, excluir_id=None):
    if codigo is None:
        return

    consulta = Promocion.objects.filter(codigo=codigo, negocio_id=negocio_id)
    if excluir_id is not None:
        consulta = consulta.exclude(pk=excluir_id)
    if consulta.exists():
        raise ValueError("Ya existe una promocion con ese codigo.")


def crear_promocion(
    *,
    negocio,
    sede_id=None,
    nombre,
    descripcion="",
    codigo=None,
    porcentaje_descuento=None,
    monto_descuento=None,
    pedido_minimo=0,
    cupo_maximo_diario=None,
    fecha_inicio,
    fecha_fin,
    productos_ids=None,
):
    nombre = str(nombre).strip()
    if not nombre:
        raise ValueError("El nombre de la promocion es obligatorio.")

    porcentaje, monto = _validar_descuento(
        porcentaje_descuento, monto_descuento
    )
    cupo = _validar_cupo(cupo_maximo_diario)
    inicio, fin = _validar_fechas(fecha_inicio, fecha_fin)
    minimo = _decimal(pedido_minimo, "pedido_minimo")
    codigo = _normalizar_codigo(codigo)
    _validar_codigo_unico(codigo, negocio.pk)
    sede = _resolver_sede(sede_id, negocio.pk)
    productos = _resolver_productos(productos_ids, negocio.pk)

    with transaction.atomic():
        promocion = Promocion.objects.create(
            negocio=negocio,
            sede=sede,
            nombre=nombre,
            descripcion=descripcion,
            codigo=codigo,
            porcentaje_descuento=porcentaje,
            monto_descuento=monto,
            pedido_minimo=minimo,
            cupo_maximo_diario=cupo,
            fecha_inicio=inicio,
            fecha_fin=fin,
        )
        PromocionProducto.objects.bulk_create(
            [
                PromocionProducto(promocion=promocion, producto=producto)
                for producto in productos
            ]
        )

        return promocion


def actualizar_promocion(promocion_id, **datos):
    with transaction.atomic():
        try:
            promocion = Promocion.objects.get(pk=promocion_id)
        except (Promocion.DoesNotExist, ValueError, TypeError):
            raise ValueError("La promocion indicada no existe.")

        if "nombre" in datos:
            nombre = str(datos["nombre"]).strip()
            if not nombre:
                raise ValueError("El nombre de la promocion es obligatorio.")
            promocion.nombre = nombre

        if "descripcion" in datos:
            promocion.descripcion = datos["descripcion"]

        if "sede_id" in datos:
            promocion.sede = _resolver_sede(datos["sede_id"], promocion.negocio_id)

        if "codigo" in datos:
            codigo = _normalizar_codigo(datos["codigo"])
            _validar_codigo_unico(
                codigo, promocion.negocio_id, excluir_id=promocion.pk
            )
            promocion.codigo = codigo

        porcentaje = datos.get(
            "porcentaje_descuento", promocion.porcentaje_descuento
        )
        monto = datos.get("monto_descuento", promocion.monto_descuento)
        promocion.porcentaje_descuento, promocion.monto_descuento = (
            _validar_descuento(porcentaje, monto)
        )

        promocion.pedido_minimo = _decimal(
            datos.get("pedido_minimo", promocion.pedido_minimo),
            "pedido_minimo",
        )
        promocion.cupo_maximo_diario = _validar_cupo(
            datos.get("cupo_maximo_diario", promocion.cupo_maximo_diario)
        )
        promocion.fecha_inicio, promocion.fecha_fin = _validar_fechas(
            datos.get("fecha_inicio", promocion.fecha_inicio),
            datos.get("fecha_fin", promocion.fecha_fin),
        )
        promocion.save()

        if "productos_ids" in datos:
            productos = _resolver_productos(
                datos["productos_ids"], promocion.negocio_id
            )
            PromocionProducto.objects.filter(
                promocion=promocion
            ).delete()
            PromocionProducto.objects.bulk_create(
                [
                    PromocionProducto(
                        promocion=promocion, producto=producto
                    )
                    for producto in productos
                ]
            )

        return promocion


def desactivar_promocion(promocion_id):
    with transaction.atomic():
        try:
            promocion = Promocion.objects.get(pk=promocion_id)
        except (Promocion.DoesNotExist, ValueError, TypeError):
            raise ValueError("La promocion indicada no existe.")

        if promocion.activa:
            promocion.activa = False
            promocion.save(update_fields=["activa"])

        return promocion


# --- Aplicación de promociones a un pedido (HU-5.3) --------------------------

CENTAVOS = Decimal("0.01")


def buscar_promocion(*, negocio_id, codigo=None, promocion_id=None, bloquear=False):
    """Encuentra la promoción por código (sin distinguir mayúsculas) o por id.

    Solo busca dentro del negocio de la sede donde se compra. Con `bloquear`
    toma la fila con select_for_update para contar el cupo sin carreras.
    """
    consulta = Promocion.objects.filter(negocio_id=negocio_id)
    if bloquear:
        consulta = consulta.select_for_update()

    codigo = _normalizar_codigo(codigo)
    try:
        if codigo:
            return consulta.get(codigo__iexact=codigo)
        if promocion_id:
            return consulta.get(pk=promocion_id)
    except (
        Promocion.DoesNotExist,
        Promocion.MultipleObjectsReturned,
        DjangoValidationError,  # uuid mal formado
        ValueError,
        TypeError,
    ):
        pass
    return None


def cupo_usado_hoy(promocion, hoy=None):
    """Pedidos no cancelados de hoy que usaron la promoción."""
    from apps.pedidos.models import EstadoPedido, Pedido

    hoy = hoy or timezone.localdate()
    return (
        Pedido.objects.filter(promocion=promocion, creado_en__date=hoy)
        .exclude(estado=EstadoPedido.CANCELADO)
        .count()
    )


def calcular_descuento_promocion(promocion, *, sede, subtotal, subtotales_por_producto, hoy=None):
    """Valida la promoción para este pedido y calcula el descuento.

    Devuelve el descuento (Decimal) o lanza ValueError con el motivo por el
    que no aplica: inactiva, de otra sede, fuera de vigencia, sin cupo hoy,
    pedido mínimo no alcanzado o sin productos aplicables en el pedido.
    """
    hoy = hoy or timezone.localdate()

    if not promocion.activa or promocion.negocio_id != sede.negocio_id:
        raise ValueError("La promoción no está disponible.")
    if promocion.sede_id and promocion.sede_id != sede.pk:
        raise ValueError("La promoción no aplica en esta sede.")
    if hoy < promocion.fecha_inicio:
        raise ValueError(
            f"La promoción empieza el {promocion.fecha_inicio:%d/%m/%Y}."
        )
    if hoy > promocion.fecha_fin:
        raise ValueError("La promoción ya no está vigente.")
    if subtotal < promocion.pedido_minimo:
        faltan = promocion.pedido_minimo - subtotal
        raise ValueError(
            f"La promoción requiere un pedido mínimo de "
            f"{formatear_pesos(promocion.pedido_minimo)}. "
            f"Te faltan {formatear_pesos(faltan)}."
        )

    aplicables = set(
        promocion.productos_aplicables.values_list("producto_id", flat=True)
    )
    if aplicables:
        base = sum(
            (valor for pid, valor in subtotales_por_producto.items() if pid in aplicables),
            Decimal("0"),
        )
        if base <= 0:
            raise ValueError(
                "La promoción no aplica a los productos de tu pedido."
            )
    else:
        base = subtotal

    if cupo_usado_hoy(promocion, hoy) >= promocion.cupo_maximo_diario:
        raise ValueError("La promoción agotó su cupo de hoy.")

    if promocion.porcentaje_descuento is not None:
        descuento = base * promocion.porcentaje_descuento / Decimal("100")
    else:
        descuento = promocion.monto_descuento
    descuento = min(descuento, base).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    return descuento


def formatear_pesos(valor):
    """$25.000 (pesos colombianos sin decimales si son enteros)."""
    valor = Decimal(valor).quantize(CENTAVOS)
    entero = int(valor)
    texto = f"{entero:,}".replace(",", ".")
    if valor != entero:
        texto += "," + f"{valor:.2f}".split(".")[1]
    return f"${texto}"
