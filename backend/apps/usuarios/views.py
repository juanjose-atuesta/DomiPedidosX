from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permission
from .serializers import RegistroClienteSerializer
from .services import registrar_cliente


class RegistroClienteView(APIView):
    permission_classes = [permission.AllowAny]

    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data
        usuario = registrar_cliente(**datos)

        return Response(
            {
                "mensaje": "Usuario registrado exitosamente",
                "id": str(usuario.id),
                "email": usuario.email,
            },
            status=status.HTTP_201_CREATED,
        )
