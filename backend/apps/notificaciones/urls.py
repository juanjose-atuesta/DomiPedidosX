from django.urls import path

from .views import (
    ConfiguracionCorreosView,
    NotificacionDetalleView,
    NotificacionListView,
    NotificacionMarcarLeidasView,
)

urlpatterns = [
    path("", NotificacionListView.as_view(), name="notificacion_list"),
    path(
        "marcar-leidas/",
        NotificacionMarcarLeidasView.as_view(),
        name="notificacion_marcar_leidas",
    ),
    path("<uuid:pk>/", NotificacionDetalleView.as_view(), name="notificacion_detalle"),
    path(
        "configuracion-correos/",
        ConfiguracionCorreosView.as_view(),
        name="configuracion_correos",
    ),
]
