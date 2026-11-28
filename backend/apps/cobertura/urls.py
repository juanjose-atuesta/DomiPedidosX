from django.urls import path

from .views import (
    CapacidadFranjaDetailView,
    CapacidadSedeView,
    VerificarCoberturaView,
    ZonaDetailView,
    ZonasSedeView,
)

urlpatterns = [
    path("sedes/<uuid:sede_id>/zonas/", ZonasSedeView.as_view(), name="zonas_sede"),
    path("zonas/<uuid:pk>/", ZonaDetailView.as_view(), name="zona_detail"),
    path("verificar/", VerificarCoberturaView.as_view(), name="verificar_cobertura"),
    # HU-9.2: capacidad por franja horaria
    path("sedes/<uuid:sede_id>/capacidad/", CapacidadSedeView.as_view(), name="capacidad_sede"),
    path("capacidad/<int:pk>/", CapacidadFranjaDetailView.as_view(), name="capacidad_detail"),
]