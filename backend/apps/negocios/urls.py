from django.urls import path

from .views import ConfiguracionCapacidadView

urlpatterns = [
    path(
        "configuracion-capacidad/",
        ConfiguracionCapacidadView.as_view(),
        name="configuracion_capacidad",
    ),
]
