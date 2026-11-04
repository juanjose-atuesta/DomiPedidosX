from django.urls import path

from .views import (
    RegistroClienteView,
    MeView,
    RegistroPersonalView,
    SolicitarPasswordResetView,
    ConfirmarPasswordResetView,
)

urlpatterns = [
    path("registro/", RegistroClienteView.as_view(), name="registro_cliente"),
    path("me/", MeView.as_view(), name="usuario_me"),
    path("personal/", RegistroPersonalView.as_view(), name="registro_personal"),
    path(
        "password-reset/",
        SolicitarPasswordResetView.as_view(),
        name="solicitar_password_reset",
    ),
    path(
        "password-reset/confirmar/",
        ConfirmarPasswordResetView.as_view(),
        name="confirmar_password_reset",
    ),
]
