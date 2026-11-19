from django.urls import path

from .views import AsignarRepartidorView, ConfiguracionRepartoView, RepartidoresSedeView

urlpatterns = [
    path(
        "sedes/<uuid:sede_id>/repartidores/",
        RepartidoresSedeView.as_view(),
        name="repartidores_sede",
    ),
    path(
        "sedes/<uuid:sede_id>/configuracion/",
        ConfiguracionRepartoView.as_view(),
        name="configuracion_reparto",
    ),
    path(
        "pedidos/<int:pk>/asignar/",
        AsignarRepartidorView.as_view(),
        name="asignar_repartidor",
    ),
]
