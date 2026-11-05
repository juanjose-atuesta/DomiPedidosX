from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador
from apps.usuarios.models import Rol

from .models import Categoria, Producto
from .serializers import (
    CategoriaSerializer,
    ComboSerializer,
    GrupoOpcionSerializer,
    ProductoSerializer,
)
from .services import (
    actualizar_categoria,
    actualizar_combo,
    actualizar_producto,
    configurar_grupo_opciones,
    crear_categoria,
    crear_combo,
    crear_producto,
    desactivar_combo,
    desactivar_producto,
)

PERMISO_GESTION = EsOperador | EsAdmin


def _es_gestor(request):
    usuario = getattr(request, "user", None)
    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
        and usuario.rol in (Rol.OPERADOR, Rol.ADMIN)
    )


def _obtener_categoria(pk):
    try:
        return Categoria.objects.get(pk=pk)
    except (Categoria.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _obtener_producto(pk):
    try:
        return (
            Producto.objects.select_related("categoria")
            .prefetch_related("grupos_opcion__opciones")
            .get(pk=pk)
        )
    except (Producto.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _obtener_combo(pk):
    try:
        return (
            Producto.objects.filter(es_combo=True)
            .prefetch_related("componentes__producto")
            .get(pk=pk)
        )
    except (Producto.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _datos_producto(validated_data):
    datos = dict(validated_data)
    if "categoria" in datos:
        categoria = datos.pop("categoria")
        datos["categoria_id"] = getattr(categoria, "pk", None)
    return datos


def _datos_combo(validated_data):
    datos = dict(validated_data)
    if "componentes" in datos:
        datos["items_combo"] = datos.pop("componentes")
    return datos


class CategoriaListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request):
        categorias = Categoria.objects.filter(activa=True).order_by(
            "orden", "nombre"
        )
        return Response(CategoriaSerializer(categorias, many=True).data)

    def post(self, request):
        serializer = CategoriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        categoria = crear_categoria(**serializer.validated_data)
        return Response(
            CategoriaSerializer(categoria).data,
            status=status.HTTP_201_CREATED,
        )


class CategoriaDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        categoria = _obtener_categoria(pk)
        if categoria is None:
            return Response(
                {"detail": "Categoria no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not categoria.activa and not _es_gestor(request):
            return Response(
                {"detail": "Categoria no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CategoriaSerializer(categoria).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        categoria = _obtener_categoria(pk)
        if categoria is None:
            return Response(
                {"detail": "Categoria no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CategoriaSerializer(
            categoria, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        categoria = actualizar_categoria(pk, **serializer.validated_data)

        return Response(CategoriaSerializer(categoria).data)

    def delete(self, request, pk):
        categoria = _obtener_categoria(pk)
        if categoria is None:
            return Response(
                {"detail": "Categoria no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        actualizar_categoria(pk, activa=False)
        return Response({"mensaje": "Categoria desactivada correctamente."})


class ProductoListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request):
        productos = (
            Producto.objects.filter(disponible=True)
            .select_related("categoria")
            .prefetch_related("grupos_opcion__opciones")
            .order_by("nombre")
        )
        return Response(ProductoSerializer(productos, many=True).data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = _datos_producto(serializer.validated_data)
        try:
            producto = crear_producto(**datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ProductoSerializer(producto).data,
            status=status.HTTP_201_CREATED,
        )


class ProductoDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        producto = _obtener_producto(pk)
        if producto is None:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not producto.disponible and not _es_gestor(request):
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ProductoSerializer(producto).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        producto = _obtener_producto(pk)
        if producto is None:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductoSerializer(
            producto, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        datos = _datos_producto(serializer.validated_data)
        try:
            producto = actualizar_producto(pk, **datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ProductoSerializer(producto).data)

    def delete(self, request, pk):
        producto = _obtener_producto(pk)
        if producto is None:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        desactivar_producto(pk)
        return Response(
            {"mensaje": "Producto desactivado correctamente."}
        )


class ProductoOpcionesView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        producto = _obtener_producto(pk)
        if producto is None:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not producto.disponible and not _es_gestor(request):
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        grupos = producto.grupos_opcion.all()
        return Response(GrupoOpcionSerializer(grupos, many=True).data)

    def post(self, request, pk):
        producto = _obtener_producto(pk)
        if producto is None:
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GrupoOpcionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        opciones = datos.pop("opciones", None)

        try:
            grupo = configurar_grupo_opciones(
                producto_id=producto.pk, **datos, opciones=opciones
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            GrupoOpcionSerializer(grupo).data,
            status=status.HTTP_201_CREATED,
        )


class ComboListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request):
        combos = (
            Producto.objects.filter(es_combo=True, disponible=True)
            .prefetch_related("componentes__producto")
            .order_by("nombre")
        )
        return Response(ComboSerializer(combos, many=True).data)

    def post(self, request):
        serializer = ComboSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = _datos_combo(serializer.validated_data)
        try:
            combo = crear_combo(**datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ComboSerializer(combo).data,
            status=status.HTTP_201_CREATED,
        )


class ComboDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [PERMISO_GESTION()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        combo = _obtener_combo(pk)
        if combo is None:
            return Response(
                {"detail": "Combo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not combo.disponible and not _es_gestor(request):
            return Response(
                {"detail": "Combo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ComboSerializer(combo).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        combo = _obtener_combo(pk)
        if combo is None:
            return Response(
                {"detail": "Combo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ComboSerializer(
            combo, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)

        datos = _datos_combo(serializer.validated_data)
        try:
            combo = actualizar_combo(pk, **datos)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(ComboSerializer(combo).data)

    def delete(self, request, pk):
        combo = _obtener_combo(pk)
        if combo is None:
            return Response(
                {"detail": "Combo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        desactivar_combo(pk)
        return Response({"mensaje": "Combo desactivado correctamente."})
