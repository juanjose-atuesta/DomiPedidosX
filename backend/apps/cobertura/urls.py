from django.urls import path

from .views import VerificarCoberturaView, ZonaDetailView, ZonasSedeView

urlpatterns = [
    path("sedes/<uuid:sede_id>/zonas/", ZonasSedeView.as_view(), name="zonas_sede"),
    path("zonas/<uuid:pk>/", ZonaDetailView.as_view(), name="zona_detail"),
    path("verificar/", VerificarCoberturaView.as_view(), name="verificar_cobertura"),
]
