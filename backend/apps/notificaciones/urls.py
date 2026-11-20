from django.urls import path

from .views import ConfiguracionCorreosView

urlpatterns = [
    path(
        "configuracion-correos/",
        ConfiguracionCorreosView.as_view(),
        name="configuracion_correos",
    ),
]
