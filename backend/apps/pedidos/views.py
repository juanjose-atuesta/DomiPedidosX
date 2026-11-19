from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import (
    EsAdmin,
    EsCliente,
    EsCocina,
    EsOperador,
    EsRepartidor,
    exigir_gestion_sede,
    exigir_operacion_sede,
)
from apps.usuarios.models import Rol

from .models import Pedido
from .serializers import (
    CambioEstadoSerializer,
    CancelarPedidoSerializer,
    PedidoCreateSerializer,
    PedidoFiltroSerializer,
    PedidoSerializer,
)
from .services import (
    cambiar_estado_pedido,
    cancelar_pedido,
    cotizar_pedido,
    crear_pedido,
    pedidos_visibles_para,
)

PERMISO_CREAR = EsCliente | EsOperador | EsAdmin
PERMISO_OPERACION = EsCocina | EsOperador | EsRepartidor | EsAdmin
PERMISO_CONSULTA = EsCliente | PERMISO_OPERACION


class PedidoListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [PERMISO_CREAR()]
        return [PERMISO_CONSULTA()]

    def get(self, request):
        filtros = PedidoFiltroSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        datos = filtros.validated_data

        pedidos = (
            pedidos_visibles_para(request.user)
            .select_related("sede__negocio")
            .prefetch_related("detalles__opciones")
        )
        if "sede" in datos:
            if request.user.rol != Rol.CLIENTE:
                exigir_operacion_sede(request.user, datos["sede"])
            pedidos = pedidos.filter(sede_id=datos["sede"])
        if "estado" in datos:
            pedidos = pedidos.filter(estado__in=datos["estado"])
        if "fecha" in datos:
            pedidos = pedidos.filter(creado_en__date=datos["fecha"])

        return Response(PedidoSerializer(pedidos, many=True).data)

    def post(self, request):
        serializer = PedidoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        detalles = datos.pop("detalles")
        sede = datos.pop("sede")
        cliente = datos.pop("cliente", None)

        if request.user.rol == Rol.CLIENTE:
            # Un cliente siempre compra a su nombre.
            cliente = request.user
        else:
            exigir_gestion_sede(request.user, sede)

        try:
            pedido = crear_pedido(
                sede=sede,
                detalles=detalles,
                cliente=cliente,
                creado_por=request.user,
                **datos,
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)})

        return Response(
            PedidoSerializer(pedido).data,
            status=status.HTTP_201_CREATED,
        )


class PedidoEstadoView(APIView):
    permission_classes = [PERMISO_OPERACION]

    def patch(self, request, pk):
        # Para un repartidor, un pedido que no puede ver es como si no existiera.
        pedidos = (
            pedidos_visibles_para(request.user)
            if request.user.rol == Rol.REPARTIDOR
            else Pedido.objects
        )
        pedido = pedidos.filter(pk=pk).first()
        if pedido is None:
            return Response(
                {"detail": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        exigir_operacion_sede(request.user, pedido.sede_id)

        serializer = CambioEstadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pedido = cambiar_estado_pedido(
                pedido.pk,
                usuario=request.user,
                **serializer.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(PedidoSerializer(pedido).data)


class PedidoCotizarView(APIView):
    """Desglose del pedido antes de confirmarlo (HU-5.2).

    Recibe lo mismo que la creación y responde subtotal, descuento de la
    promoción, costo de domicilio según la zona y total, más los problemas
    que impedirían confirmarlo (sede cerrada, fuera de cobertura, mínimo...).
    """

    permission_classes = [PERMISO_CREAR]

    def post(self, request):
        serializer = PedidoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        if request.user.rol != Rol.CLIENTE:
            exigir_gestion_sede(request.user, datos["sede"])

        try:
            cotizacion = cotizar_pedido(
                sede=datos["sede"],
                detalles=datos["detalles"],
                tipo=datos["tipo"],
                entrega_lat=datos.get("entrega_lat"),
                entrega_lng=datos.get("entrega_lng"),
                codigo_promocion=datos.get("codigo_promocion", ""),
                promocion_id=datos.get("promocion_id"),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)})

        zona = cotizacion["zona"]
        promocion = cotizacion["promocion"]
        return Response(
            {
                "subtotal": f"{cotizacion['subtotal']:.2f}",
                "descuento": f"{cotizacion['descuento']:.2f}",
                "costo_domicilio": f"{cotizacion['costo_domicilio']:.2f}",
                "total": f"{cotizacion['total']:.2f}",
                "tiempo_estimado_min": cotizacion["tiempo_estimado_min"],
                "zona": zona
                and {
                    "id": str(zona.pk),
                    "nombre": zona.nombre,
                    "pedido_minimo": f"{zona.pedido_minimo:.2f}",
                    "tiempo_estimado_min": zona.tiempo_estimado_min,
                },
                "promocion": promocion
                and {
                    "id": str(promocion.pk),
                    "nombre": promocion.nombre,
                    "codigo": promocion.codigo,
                },
                "error_promocion": cotizacion["error_promocion"],
                "problemas": cotizacion["problemas"],
                "puede_confirmar": not cotizacion["problemas"],
            }
        )


class PedidoCancelarView(APIView):
    """El cliente cancela su propio pedido mientras está en Recibido (HU-5.6)."""

    permission_classes = [EsCliente]

    def post(self, request, pk):
        if not Pedido.objects.filter(pk=pk, cliente=request.user).exists():
            return Response(
                {"detail": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CancelarPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pedido = cancelar_pedido(
                pk, usuario=request.user, motivo=serializer.validated_data["motivo"]
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PedidoSerializer(pedido).data)
