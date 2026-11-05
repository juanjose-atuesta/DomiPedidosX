from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador
from apps.sedes.models import Sede

from .models import InventarioSede
from .serializers import InventarioSedeSerializer
from .services import (
    asignar_o_actualizar_inventario_sede,
    cambiar_disponibilidad_producto_sede,
)

PERMISO_GESTION = EsOperador | EsAdmin


def _obtener_sede(pk):
    try:
        return Sede.objects.get(pk=pk)
    except (Sede.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _obtener_inventario(sede_id, producto_id):
    try:
        return (
            InventarioSede.objects.select_related("producto")
            .filter(sede_id=sede_id, producto_id=producto_id)
            .first()
        )
    except (DjangoValidationError, ValueError, TypeError):
        return None


class InventarioSedeView(APIView):
    def get_permissions(self):
        return [PERMISO_GESTION()]

    def get(self, request, sede_id):
        sede = _obtener_sede(sede_id)
        if sede is None:
            return Response(
                {"detail": "Sede no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        inventarios = (
            InventarioSede.objects.filter(sede=sede)
            .select_related("producto")
            .order_by("producto__nombre")
        )
        return Response(
            InventarioSedeSerializer(inventarios, many=True).data
        )

    def post(self, request, sede_id):
        serializer = InventarioSedeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        producto = datos.pop("producto")
        try:
            inventario = asignar_o_actualizar_inventario_sede(
                sede_id=sede_id,
                producto_id=producto.pk,
                **datos,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        codigo = (
            status.HTTP_201_CREATED
            if getattr(inventario, "_fue_creado", False)
            else status.HTTP_200_OK
        )
        return Response(
            InventarioSedeSerializer(inventario).data,
            status=codigo,
        )

    def put(self, request, sede_id):
        return self._actualizar(request, sede_id, partial=False)

    def patch(self, request, sede_id):
        return self._actualizar(request, sede_id, partial=True)

    def delete(self, request, sede_id):
        producto_id = request.data.get(
            "producto_id"
        ) or request.query_params.get("producto_id")
        if not producto_id:
            return Response(
                {
                    "producto_id": [
                        "Este campo es obligatorio para eliminar el inventario."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventario = _obtener_inventario(sede_id, producto_id)
        if inventario is None:
            return Response(
                {"detail": "Inventario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        inventario.delete()
        return Response(
            {"mensaje": "Inventario eliminado correctamente."}
        )

    def _actualizar(self, request, sede_id, *, partial):
        producto_id = request.data.get("producto_id")
        if not producto_id:
            return Response(
                {
                    "producto_id": [
                        "Este campo es obligatorio para actualizar el inventario."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventario = _obtener_inventario(sede_id, producto_id)
        if inventario is None:
            return Response(
                {"detail": "Inventario no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InventarioSedeSerializer(
            inventario, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        producto = datos.pop("producto", inventario.producto)

        if partial and set(datos) == {"disponible_en_sede"}:
            try:
                inventario = cambiar_disponibilidad_producto_sede(
                    sede_id=sede_id,
                    producto_id=producto.pk,
                    disponible=datos["disponible_en_sede"],
                )
            except ValueError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            campos = {
                "disponible_en_sede": datos.get(
                    "disponible_en_sede", inventario.disponible_en_sede
                ),
                "controla_stock": datos.get(
                    "controla_stock", inventario.controla_stock
                ),
                "stock_actual": datos.get(
                    "stock_actual", inventario.stock_actual
                ),
                "stock_minimo": datos.get(
                    "stock_minimo", inventario.stock_minimo
                ),
            }
            try:
                inventario = asignar_o_actualizar_inventario_sede(
                    sede_id=sede_id,
                    producto_id=producto.pk,
                    **campos,
                )
            except ValueError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(InventarioSedeSerializer(inventario).data)
