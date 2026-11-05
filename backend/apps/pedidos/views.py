from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsCliente, EsOperador
from apps.usuarios.models import Rol

from .serializers import PedidoCreateSerializer, PedidoSerializer
from .services import crear_pedido

PERMISO_PEDIDOS = EsCliente | EsOperador | EsAdmin


class PedidoListCreateView(APIView):
    permission_classes = [PERMISO_PEDIDOS]

    def post(self, request):
        serializer = PedidoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        detalles = datos.pop("detalles")
        sede = datos.pop("sede")

        cliente = None
        if request.user.rol == Rol.CLIENTE:
            cliente = request.user

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
