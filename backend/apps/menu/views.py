from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador, exigir_negocio
from apps.inventario.models import InventarioSede
from apps.sedes.models import Sede
from apps.usuarios.models import Rol

from .models import Categoria, Producto
from .serializers import (
    CategoriaSerializer,
    ComboSerializer,
    GrupoOpcionSerializer,
    ProductoCatalogoSedeSerializer,
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


def _gestiona(request, objeto):
    """El objeto pertenece al negocio de quien lo gestiona."""
    return (
        objeto is not None
        and _es_gestor(request)
        and bool(request.user.negocio_id)
        and objeto.negocio_id == request.user.negocio_id
    )


def _filtrar_por_negocio(request, consulta):
    """El personal ve solo su negocio; el público puede filtrar con ?negocio=<id>."""
    usuario = request.user
    if usuario.is_authenticated and usuario.rol != Rol.CLIENTE:
        return consulta.filter(negocio_id=usuario.negocio_id)

    consulta = consulta.filter(negocio__activo=True)
    negocio = request.query_params.get("negocio", "").strip()
    if not negocio:
        return consulta
    try:
        return consulta.filter(negocio_id=UUID(negocio))
    except ValueError:
        raise serializers.ValidationError({"negocio": "Identificador no válido."})


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
        categorias = _filtrar_por_negocio(
            request, Categoria.objects.filter(activa=True)
        ).order_by("orden", "nombre")
        return Response(CategoriaSerializer(categorias, many=True).data)

    def post(self, request):
        serializer = CategoriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        categoria = crear_categoria(
            negocio=exigir_negocio(request.user), **serializer.validated_data
        )
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

        if not categoria.activa and not _gestiona(request, categoria):
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
        if not _gestiona(request, categoria):
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
        if not _gestiona(request, categoria):
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
            _filtrar_por_negocio(request, Producto.objects.all())
            .select_related("categoria")
            .prefetch_related("grupos_opcion__opciones")
            .order_by("nombre")
        )
        incluir = request.query_params.get("incluir_inactivos", "")
        if not (_es_gestor(request) and incluir.strip().lower() == "true"):
            productos = productos.filter(disponible=True)
        return Response(ProductoSerializer(productos, many=True).data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = _datos_producto(serializer.validated_data)
        try:
            producto = crear_producto(
                negocio=exigir_negocio(request.user), **datos
            )
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

        if not producto.disponible and not _gestiona(request, producto):
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
        if not _gestiona(request, producto):
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
        if not _gestiona(request, producto):
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

        if not producto.disponible and not _gestiona(request, producto):
            return Response(
                {"detail": "Producto no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        grupos = producto.grupos_opcion.all()
        return Response(GrupoOpcionSerializer(grupos, many=True).data)

    def post(self, request, pk):
        producto = _obtener_producto(pk)
        if not _gestiona(request, producto):
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
            _filtrar_por_negocio(
                request, Producto.objects.filter(es_combo=True, disponible=True)
            )
            .prefetch_related("componentes__producto")
            .order_by("nombre")
        )
        return Response(ComboSerializer(combos, many=True).data)

    def post(self, request):
        serializer = ComboSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = _datos_combo(serializer.validated_data)
        try:
            combo = crear_combo(negocio=exigir_negocio(request.user), **datos)
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

        if not combo.disponible and not _gestiona(request, combo):
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
        if not _gestiona(request, combo):
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
        if not _gestiona(request, combo):
            return Response(
                {"detail": "Combo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        desactivar_combo(pk)
        return Response({"mensaje": "Combo desactivado correctamente."})


class CatalogoSedeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, sede_id):
        sede = Sede.objects.filter(
            pk=sede_id, activa=True, negocio__activo=True
        ).first()
        if sede is None:
            return Response(
                {"detail": "Sede no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        inventarios = (
            InventarioSede.objects.filter(
                sede=sede,
                disponible_en_sede=True,
                producto__disponible=True,
            )
            .select_related("producto")
            .prefetch_related("producto__grupos_opcion__opciones")
            .order_by("producto__nombre")
        )

        productos = []
        for inventario in inventarios:
            producto = inventario.producto
            producto.agotado = inventario.agotado
            productos.append(producto)

        return Response(
            ProductoCatalogoSedeSerializer(productos, many=True).data
        )
