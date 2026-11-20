from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.dateparse import parse_date
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador, exigir_negocio
from apps.usuarios.models import Rol

from .models import Feriado, Sede
from .serializers import FeriadoSerializer, SedeSerializer
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


# --- Feriados (HU-8.9) -------------------------------------------------------


class FeriadoListCreateView(APIView):
    """Feriados del negocio. El operador los consulta; el admin los gestiona.

    `?desde=AAAA-MM-DD` filtra los de esa fecha en adelante.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdmin()]
        return [(EsAdmin | EsOperador)()]

    def get(self, request):
        negocio = exigir_negocio(request.user)
        feriados = Feriado.objects.filter(negocio=negocio).prefetch_related("sedes")
        desde = parse_date(request.query_params.get("desde") or "")
        if desde:
            feriados = feriados.filter(fecha__gte=desde)
        return Response(FeriadoSerializer(feriados, many=True).data)

    def post(self, request):
        negocio = exigir_negocio(request.user)
        serializer = FeriadoSerializer(
            data=request.data, context={"negocio_id": negocio.pk}
        )
        serializer.is_valid(raise_exception=True)
        feriado = serializer.save(negocio=negocio)
        return Response(FeriadoSerializer(feriado).data, status=status.HTTP_201_CREATED)


class FeriadoDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obtener(self, request, pk):
        negocio = exigir_negocio(request.user)
        return Feriado.objects.filter(pk=pk, negocio=negocio).first()

    def get(self, request, pk):
        feriado = self._obtener(request, pk)
        if feriado is None:
            return Response({"detail": "Feriado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(FeriadoSerializer(feriado).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        feriado = self._obtener(request, pk)
        if feriado is None:
            return Response({"detail": "Feriado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = FeriadoSerializer(
            feriado,
            data=request.data,
            partial=partial,
            context={"negocio_id": feriado.negocio_id},
        )
        serializer.is_valid(raise_exception=True)
        feriado = serializer.save()
        return Response(FeriadoSerializer(feriado).data)

    def delete(self, request, pk):
        feriado = self._obtener(request, pk)
        if feriado is None:
            return Response({"detail": "Feriado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        feriado.delete()
        return Response({"mensaje": "Feriado eliminado."})
