import uuid
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import EsAdmin, EsOperador, exigir_operacion_sede
from apps.sedes.models import Sede
from apps.usuarios.models import Rol

from .models import ZonaCobertura
from .serializers import ZonaCoberturaSerializer, ZonaPublicaSerializer
from .services import zonas_que_cubren, ocupacion_por_franja

from .serializers import CapacidadFranjaSerializer
from .models import CapacidadFranja

NO_ENCONTRADA = {"detail": "Zona no encontrada."}
NO_ENCONTRADA_FRANJA = {"detail": "Franja no encontrada."}


def _sede_del_negocio(request, sede_id):
    """Sede del negocio del usuario; las de otro negocio son como si no existieran."""
    try:
        return Sede.objects.get(pk=sede_id, negocio_id=request.user.negocio_id)
    except (Sede.DoesNotExist, DjangoValidationError, ValueError):
        return None


def _zona_del_negocio(request, pk):
    try:
        return ZonaCobertura.objects.select_related("sede").get(
            pk=pk, sede__negocio_id=request.user.negocio_id
        )
    except (ZonaCobertura.DoesNotExist, DjangoValidationError, ValueError):
        return None


class ZonasSedeView(APIView):
    """Zonas de cobertura de una sede (HU-8.4).

    El admin las crea y edita; el operador de la sede solo las consulta.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdmin()]
        return [(EsAdmin | EsOperador)()]

    def get(self, request, sede_id):
        sede = _sede_del_negocio(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.rol == Rol.OPERADOR:
            exigir_operacion_sede(request.user, sede)
        zonas = sede.zonas.select_related("sede").order_by("-activa", "nombre")
        return Response(ZonaCoberturaSerializer(zonas, many=True).data)

    def post(self, request, sede_id):
        sede = _sede_del_negocio(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ZonaCoberturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zona = serializer.save(sede=sede)
        return Response(
            ZonaCoberturaSerializer(zona).data, status=status.HTTP_201_CREATED
        )


class ZonaDetailView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request, pk):
        zona = _zona_del_negocio(request, pk)
        if zona is None:
            return Response(NO_ENCONTRADA, status=status.HTTP_404_NOT_FOUND)
        return Response(ZonaCoberturaSerializer(zona).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        zona = _zona_del_negocio(request, pk)
        if zona is None:
            return Response(NO_ENCONTRADA, status=status.HTTP_404_NOT_FOUND)
        serializer = ZonaCoberturaSerializer(zona, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        zona = serializer.save()
        return Response(ZonaCoberturaSerializer(zona).data)

    def delete(self, request, pk):
        """Borrado lógico: los pedidos anteriores conservan su zona."""
        zona = _zona_del_negocio(request, pk)
        if zona is None:
            return Response(NO_ENCONTRADA, status=status.HTTP_404_NOT_FOUND)
        zona.activa = False
        zona.save(update_fields=["activa", "actualizado_en"])
        return Response({"mensaje": "Zona desactivada correctamente."})


class VerificarCoberturaView(APIView):
    """Público: ¿qué sedes llegan a este punto? ?lat=&lng=[&sede=]"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = Decimal(request.query_params.get("lat", ""))
            lng = Decimal(request.query_params.get("lng", ""))
        except (InvalidOperation, TypeError):
            return Response(
                {"detail": "Indica lat y lng numéricos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return Response(
                {"detail": "Coordenadas fuera de rango."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sedes = None
        sede_id = request.query_params.get("sede")
        if sede_id:
            sedes = Sede.objects.filter(pk=sede_id) if _es_uuid(sede_id) else Sede.objects.none()

        zonas = zonas_que_cubren(lat, lng, sedes=sedes)
        return Response(
            {
                "cubierta": bool(zonas),
                "zonas": ZonaPublicaSerializer(zonas, many=True).data,
            }
        )


def _es_uuid(valor):
    try:
        uuid.UUID(str(valor))
    except ValueError:
        return False
    return True


class CapacidadSedeView(APIView):
    """Franjas de capacidad de una sede (HU-9.2).

    El operador define el tope de pedidos simultáneos por franja de 1 hora para
    su propia sede; el admin puede hacerlo en cualquier sede de su negocio.
    """

    permission_classes = [EsOperador]

    def _sede(self, request, sede_id):
        sede = _sede_del_negocio(request, sede_id)
        if sede is None:
            return None
        if request.user.rol == Rol.OPERADOR:
            exigir_operacion_sede(request.user, sede)
        return sede

    def get(self, request, sede_id):
        sede = self._sede(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        franjas = list(sede.franjas_capacidad.filter(activa=True).order_by("dia_semana", "hora_inicio"))
        contexto = {"ocupacion": ocupacion_por_franja(sede, franjas)}
        return Response(
            {
                "sede_id": str(sede.pk),
                "tope_general": sede.tope_general_pedidos,
                "franjas": CapacidadFranjaSerializer(franjas, many=True, context=contexto).data,
            }
        )

    def post(self, request, sede_id):
        sede = self._sede(request, sede_id)
        if sede is None:
            return Response({"detail": "Sede no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CapacidadFranjaSerializer(data=request.data, context={"sede": sede})
        serializer.is_valid(raise_exception=True)
        franja = serializer.save(sede=sede)
        return Response(CapacidadFranjaSerializer(franja).data, status=status.HTTP_201_CREATED)


class CapacidadFranjaDetailView(APIView):
    permission_classes = [EsAdmin | EsOperador]

    def _franja(self, request, pk):
        try:
            franja = CapacidadFranja.objects.select_related("sede").get(
                pk=pk, activa=True, sede__negocio_id=request.user.negocio_id
            )
        except (CapacidadFranja.DoesNotExist, ValueError):
            return None
        if request.user.rol == Rol.OPERADOR:
            exigir_operacion_sede(request.user, franja.sede)
        return franja

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, *, partial):
        franja = self._franja(request, pk)
        if franja is None:
            return Response(NO_ENCONTRADA_FRANJA, status=status.HTTP_404_NOT_FOUND)
        serializer = CapacidadFranjaSerializer(
            franja, data=request.data, partial=partial, context={"sede": franja.sede}
        )
        serializer.is_valid(raise_exception=True)
        return Response(CapacidadFranjaSerializer(serializer.save()).data)

    def delete(self, request, pk):
        """Borrado lógico: la franja deja de aplicar y se puede volver a crear."""
        franja = self._franja(request, pk)
        if franja is None:
            return Response(NO_ENCONTRADA_FRANJA, status=status.HTTP_404_NOT_FOUND)
        franja.activa = False
        franja.save(update_fields=["activa"])
        return Response({"mensaje": "Franja eliminada correctamente."})
