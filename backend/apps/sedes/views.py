from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, exigir_negocio
from apps.usuarios.models import Rol

from .models import Sede
from .serializers import SedeSerializer
from .services import (
    actualizar_sede,
    crear_sede,
    desactivar_sede,
    reactivar_sede,
)

MENSAJE_SEDE_NO_ENCONTRADA = "Sede no encontrada."


def _es_admin_autenticado(request):
    usuario = getattr(request, "user", None)
    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
        and usuario.rol == Rol.ADMIN
    )


def _es_personal(request):
    usuario = getattr(request, "user", None)
    return bool(usuario and usuario.is_authenticated and usuario.rol != Rol.CLIENTE)


def _es_de_su_negocio(request, sede):
    """Sedes que un admin puede gestionar; las de otro negocio son como si no existieran."""
    return (
        sede is not None
        and bool(request.user.negocio_id)
        and sede.negocio_id == request.user.negocio_id
    )


def _solicita_incluir_inactivas(request):
    valor = request.query_params.get("incluir_inactivas", "")
    return valor.strip().lower() in {"1", "true", "si", "sí"}


def _obtener_sede(pk):
    try:
        return Sede.objects.select_related("negocio").prefetch_related("horarios").get(pk=pk)
    except (Sede.DoesNotExist, DjangoValidationError, ValueError):
        return None


class SedeListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdmin()]
        return [permissions.AllowAny()]

    def get(self, request):
        sedes = Sede.objects.select_related("negocio").prefetch_related("horarios")

        # El personal solo ve su negocio; el público, las sedes de todos.
        if _es_personal(request):
            sedes = sedes.filter(negocio_id=request.user.negocio_id)
        else:
            sedes = sedes.filter(negocio__activo=True)

        ver_inactivas = (
            _es_admin_autenticado(request)
            and _solicita_incluir_inactivas(request)
        )
        if not ver_inactivas:
            sedes = sedes.filter(activa=True)

        sedes = sedes.order_by("nombre")
        return Response(SedeSerializer(sedes, many=True).data)

    def post(self, request):
        serializer = SedeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        horarios = datos.pop("horarios", [])

        try:
            sede = crear_sede(
                negocio=exigir_negocio(request.user), **datos, horarios=horarios
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            SedeSerializer(sede).data, status=status.HTTP_201_CREATED
        )


class SedeDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [EsAdmin()]
        return [permissions.AllowAny()]

    def get(self, request, pk):
        sede = _obtener_sede(pk)
        if sede is None:
            return Response(
                {"detail": MENSAJE_SEDE_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not sede.activa and not (
            _es_admin_autenticado(request) and _es_de_su_negocio(request, sede)
        ):
            return Response(
                {"detail": MENSAJE_SEDE_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SedeSerializer(sede).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        sede = _obtener_sede(pk)
        if not _es_de_su_negocio(request, sede):
            return Response(
                {"detail": MENSAJE_SEDE_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SedeSerializer(sede, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        datos = dict(serializer.validated_data)
        horarios = datos.pop("horarios", None)

        try:
            sede = actualizar_sede(sede, datos_sede=datos, horarios=horarios)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(SedeSerializer(sede).data)

    def delete(self, request, pk):
        sede = _obtener_sede(pk)
        if not _es_de_su_negocio(request, sede):
            return Response(
                {"detail": MENSAJE_SEDE_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        desactivar_sede(sede)
        return Response({"mensaje": "Sede desactivada correctamente."})


class SedeReactivarView(APIView):
    permission_classes = [EsAdmin]

    def post(self, request, pk):
        sede = _obtener_sede(pk)
        if not _es_de_su_negocio(request, sede):
            return Response(
                {"detail": MENSAJE_SEDE_NO_ENCONTRADA},
                status=status.HTTP_404_NOT_FOUND,
            )

        sede = reactivar_sede(sede)
        return Response(
            {
                "mensaje": "Sede reactivada correctamente.",
                "sede": SedeSerializer(sede).data,
            }
        )
