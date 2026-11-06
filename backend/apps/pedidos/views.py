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
    PedidoCreateSerializer,
    PedidoFiltroSerializer,
    PedidoSerializer,
)
from .services import cambiar_estado_pedido, crear_pedido, pedidos_visibles_para

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
            # Un cliente siempre compra a su nombre y no fija su propio descuento.
            cliente = request.user
            datos.pop("descuento", None)
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
