from django.urls import path

from .views import VentasSedeZonaView

urlpatterns = [
    path("ventas-sede-zona/", VentasSedeZonaView.as_view(), name="reporte_ventas_sede_zona"),
]