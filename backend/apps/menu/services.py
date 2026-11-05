from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import (
    Categoria,
    GrupoOpcion,
    OpcionProducto,
    Producto,
    ProductoCombo,
    TipoGrupoOpcion,
)

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


def _resolver_producto(valor):
    if isinstance(valor, Producto):
        return valor
    return _obtener_producto(valor)


def _normalizar_items_combo(items_combo):
    if not items_combo:
        raise ValueError("El combo debe incluir al menos un producto.")

    items_normalizados = []
    productos_vistos = set()

    for item in items_combo:
        if not isinstance(item, dict):
            raise ValueError("Cada componente del combo debe ser un objeto.")

        producto = item.get("producto")
        if producto is None:
            producto = item.get("producto_id")
        producto = _resolver_producto(producto)

        if producto.pk in productos_vistos:
            raise ValueError("No se puede repetir un producto en el combo.")

        cantidad = _entero_positivo(
            item.get("cantidad", 1), "cantidad del componente"
        )

        productos_vistos.add(producto.pk)
        items_normalizados.append(
            {"producto": producto, "cantidad": cantidad}
        )

    return items_normalizados


def _validar_sin_ciclos(combo_id):
    en_camino = set()
    visitados = set()

    def visitar(producto_id):
        if producto_id in en_camino:
            raise ValueError("El combo no puede contener ciclos.")
        if producto_id in visitados:
            return

        en_camino.add(producto_id)
        componentes = ProductoCombo.objects.filter(
            combo_id=producto_id
        ).values_list("producto_id", flat=True)

        for componente_id in componentes:
            visitar(componente_id)

        en_camino.remove(producto_id)
        visitados.add(producto_id)

    visitar(combo_id)


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


def crear_combo(
    *,
    nombre,
    descripcion="",
    precio_base,
    items_combo,
):
    nombre = str(nombre).strip()
    if not nombre:
        raise ValueError("El nombre del combo es obligatorio.")

    precio = _decimal_no_negativo(precio_base, "precio_base")
    items_normalizados = _normalizar_items_combo(items_combo)

    with transaction.atomic():
        combo = Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio,
            es_combo=True,
        )
        ProductoCombo.objects.bulk_create(
            [
                ProductoCombo(
                    combo=combo,
                    producto=item["producto"],
                    cantidad=item["cantidad"],
                )
                for item in items_normalizados
            ]
        )
        _validar_sin_ciclos(combo.pk)

        return combo


def actualizar_combo(combo_id, **datos):
    with transaction.atomic():
        combo = _obtener_producto(combo_id)
        if not combo.es_combo:
            raise ValueError("El producto indicado no es un combo.")

        campos_actualizados = []

        if "nombre" in datos:
            nombre = str(datos["nombre"]).strip()
            if not nombre:
                raise ValueError("El nombre del combo es obligatorio.")
            combo.nombre = nombre
            campos_actualizados.append("nombre")

        if "descripcion" in datos:
            combo.descripcion = datos["descripcion"]
            campos_actualizados.append("descripcion")

        if "precio_base" in datos:
            combo.precio_base = _decimal_no_negativo(
                datos["precio_base"], "precio_base"
            )
            campos_actualizados.append("precio_base")

        if campos_actualizados:
            combo.save(update_fields=campos_actualizados)

        if "items_combo" in datos and datos["items_combo"] is not None:
            items_normalizados = _normalizar_items_combo(
                datos["items_combo"]
            )
            if any(
                item["producto"].pk == combo.pk
                for item in items_normalizados
            ):
                raise ValueError("Un combo no puede incluirse a si mismo.")
            ProductoCombo.objects.filter(combo=combo).delete()
            ProductoCombo.objects.bulk_create(
                [
                    ProductoCombo(
                        combo=combo,
                        producto=item["producto"],
                        cantidad=item["cantidad"],
                    )
                    for item in items_normalizados
                ]
            )
            _validar_sin_ciclos(combo.pk)

        return combo


def desactivar_combo(combo_id):
    with transaction.atomic():
        combo = _obtener_producto(combo_id)
        if not combo.es_combo:
            raise ValueError("El producto indicado no es un combo.")

        if combo.disponible:
            combo.disponible = False
            combo.save(update_fields=["disponible"])

        return combo


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
