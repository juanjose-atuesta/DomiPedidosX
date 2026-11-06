from rest_framework import serializers

from .models import (
    Categoria,
    GrupoOpcion,
    OpcionProducto,
    Producto,
    ProductoCombo,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nombre", "descripcion", "orden", "activa")
        read_only_fields = ("id",)


class OpcionProductoSerializer(serializers.ModelSerializer):
    precio_adicional = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
    )

    class Meta:
        model = OpcionProducto
        fields = (
            "id",
            "nombre",
            "precio_adicional",
            "activa",
            "orden",
        )
        read_only_fields = ("id",)


class GrupoOpcionSerializer(serializers.ModelSerializer):
    opciones = OpcionProductoSerializer(many=True, required=False)
    max_selecciones = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = GrupoOpcion
        fields = (
            "id",
            "producto",
            "nombre",
            "tipo",
            "obligatorio",
            "max_selecciones",
            "orden",
            "opciones",
        )
        read_only_fields = ("id", "producto")


class ProductoSerializer(serializers.ModelSerializer):
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria",
        queryset=Categoria.objects.all(),
        required=False,
        allow_null=True,
    )
    precio_base = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    tiempo_preparacion_min = serializers.IntegerField(min_value=1)
    grupos_opcion = GrupoOpcionSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id",
            "categoria_id",
            "nombre",
            "descripcion",
            "precio_base",
            "imagen_url",
            "tiempo_preparacion_min",
            "es_combo",
            "disponible",
            "grupos_opcion",
        )
        read_only_fields = ("id", "grupos_opcion")


class ProductoCatalogoSedeSerializer(ProductoSerializer):
    agotado = serializers.BooleanField(read_only=True)

    class Meta(ProductoSerializer.Meta):
        fields = ProductoSerializer.Meta.fields + ("agotado",)


class ItemComboSerializer(serializers.ModelSerializer):
    producto_id = serializers.PrimaryKeyRelatedField(
        source="producto",
        queryset=Producto.objects.all(),
    )
    producto_nombre = serializers.CharField(
        source="producto.nombre", read_only=True
    )
    cantidad = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = ProductoCombo
        fields = ("producto_id", "producto_nombre", "cantidad")


class ComboSerializer(serializers.ModelSerializer):
    precio_base = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    items_combo = ItemComboSerializer(
        source="componentes",
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Producto
        fields = (
            "id",
            "nombre",
            "descripcion",
            "precio_base",
            "es_combo",
            "disponible",
            "items_combo",
        )
        read_only_fields = ("id", "es_combo", "disponible")
