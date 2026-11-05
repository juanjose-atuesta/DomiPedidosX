from django.urls import path
from .views import (
    # Develop
    RegistroClienteView,
    LoginView,
    MeView,
    RegistroPersonalView,
    SolicitarPasswordResetView,
    ConfirmarPasswordResetView,
    # Tuyas
    DesactivarUsuarioView,
    CambiarRolView,
    DireccionListCreateView,
)

urlpatterns = [
    # Rutas de Develop
    path("registro/", RegistroClienteView.as_view(), name="registro_cliente"),
    path("login/", LoginView.as_view(), name="login"),
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
    # Tus rutas
    path("usuarios/<uuid:pk>/desactivar/", DesactivarUsuarioView.as_view(), name="desactivar-usuario"),
    path("usuarios/<uuid:pk>/cambiar-rol/", CambiarRolView.as_view(), name="cambiar-rol"),
    path("direcciones/", DireccionListCreateView.as_view(), name="direcciones"),
]
