from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Categoria, GrupoOpcion, OpcionProducto, Producto, TipoGrupoOpcion

CAMPOS_CATEGORIA = ("nombre", "descripcion", "orden", "activa")
CAMPOS_PRODUCTO_SIMPLES = (
    "nombre",
    "descripcion",
    "imagen_url",
    "es_combo",
    "disponible",
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


def _obtener_categoria(categoria_id):
    try:
        return Categoria.objects.get(pk=categoria_id)
    except (Categoria.DoesNotExist, ValueError, TypeError):
        raise ValueError("La categoria indicada no existe.")


def _obtener_producto(producto_id):
    try:
        return Producto.objects.get(pk=producto_id)
    except (Producto.DoesNotExist, ValueError, TypeError):
        raise ValueError("El producto indicado no existe.")


def _normalizar_opcion(opcion):
    if not isinstance(opcion, dict):
        raise ValueError("Cada opcion debe ser un objeto.")

    nombre = str(opcion.get("nombre", "")).strip()
    if not nombre:
        raise ValueError("Cada opcion debe tener un nombre.")

    precio = _decimal_no_negativo(
        opcion.get("precio_adicional", 0), "precio_adicional"
    )

    try:
        orden = int(opcion.get("orden", 0))
    except (TypeError, ValueError):
        raise ValueError("El orden de la opcion debe ser un entero valido.")

    return {
        "nombre": nombre,
        "precio_adicional": precio,
        "activa": bool(opcion.get("activa", True)),
        "orden": orden,
    }


def crear_categoria(*, nombre, descripcion="", orden=0, activa=True):
    with transaction.atomic():
        return Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            orden=orden,
            activa=activa,
        )


def actualizar_categoria(categoria_id, **datos):
    with transaction.atomic():
        categoria = _obtener_categoria(categoria_id)

        campos_actualizados = []
        for campo in CAMPOS_CATEGORIA:
            if campo not in datos:
                continue
            setattr(categoria, campo, datos[campo])
            campos_actualizados.append(campo)

        if campos_actualizados:
            categoria.save(update_fields=campos_actualizados)

        return categoria


def crear_producto(
    *,
    categoria_id=None,
    nombre,
    descripcion="",
    precio_base,
    imagen_url="",
    tiempo_preparacion_min,
    es_combo=False,
):
    precio = _decimal_no_negativo(precio_base, "precio_base")
    tiempo = _entero_positivo(
        tiempo_preparacion_min, "tiempo_preparacion_min"
    )

    if categoria_id is not None:
        _obtener_categoria(categoria_id)

    with transaction.atomic():
        return Producto.objects.create(
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio,
            imagen_url=imagen_url,
            tiempo_preparacion_min=tiempo,
            es_combo=es_combo,
        )


def actualizar_producto(producto_id, **datos):
    with transaction.atomic():
        producto = _obtener_producto(producto_id)
        campos_actualizados = []

        if "categoria_id" in datos:
            categoria_id = datos["categoria_id"]
            if categoria_id is not None:
                _obtener_categoria(categoria_id)
            producto.categoria_id = categoria_id
            campos_actualizados.append("categoria_id")

        if "precio_base" in datos:
            producto.precio_base = _decimal_no_negativo(
                datos["precio_base"], "precio_base"
            )
            campos_actualizados.append("precio_base")

        if "tiempo_preparacion_min" in datos:
            producto.tiempo_preparacion_min = _entero_positivo(
                datos["tiempo_preparacion_min"], "tiempo_preparacion_min"
            )
            campos_actualizados.append("tiempo_preparacion_min")

        for campo in CAMPOS_PRODUCTO_SIMPLES:
            if campo not in datos:
                continue
            setattr(producto, campo, datos[campo])
            campos_actualizados.append(campo)

        if campos_actualizados:
            producto.save(update_fields=campos_actualizados)

        return producto


def desactivar_producto(producto_id):
    with transaction.atomic():
        producto = _obtener_producto(producto_id)
        if producto.disponible:
            producto.disponible = False
            producto.save(update_fields=["disponible"])
        return producto


def configurar_grupo_opciones(
    *,
    producto_id,
    nombre,
    tipo,
    obligatorio=False,
    max_selecciones=1,
    opciones=None,
    orden=0,
):
    nombre = str(nombre).strip()
    if not nombre:
        raise ValueError("El nombre del grupo es obligatorio.")

    if tipo not in TipoGrupoOpcion.values:
        raise ValueError("El tipo de grupo no es valido.")

    max_selecciones = _entero_positivo(
        max_selecciones, "max_selecciones"
    )

    try:
        orden = int(orden)
    except (TypeError, ValueError):
        raise ValueError("El orden del grupo debe ser un entero valido.")

    opciones_normalizadas = None
    if opciones is not None:
        opciones_normalizadas = [
            _normalizar_opcion(opcion) for opcion in opciones
        ]

    with transaction.atomic():
        producto = _obtener_producto(producto_id)
        grupo = GrupoOpcion.objects.filter(
            producto=producto, nombre=nombre
        ).first()

        if grupo is None:
            grupo = GrupoOpcion.objects.create(
                producto=producto,
                nombre=nombre,
                tipo=tipo,
                obligatorio=obligatorio,
                max_selecciones=max_selecciones,
                orden=orden,
            )
        else:
            grupo.tipo = tipo
            grupo.obligatorio = obligatorio
            grupo.max_selecciones = max_selecciones
            grupo.orden = orden
            grupo.save(
                update_fields=[
                    "tipo",
                    "obligatorio",
                    "max_selecciones",
                    "orden",
                ]
            )

        if opciones_normalizadas is not None:
            grupo.opciones.all().delete()
            OpcionProducto.objects.bulk_create(
                [
                    OpcionProducto(grupo=grupo, **opcion)
                    for opcion in opciones_normalizadas
                ]
            )

        return grupo
