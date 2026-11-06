from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    ModuloCocinaView,
    ModuloRepartidorView,
    ModuloSedeView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    # Recibe {"refresh": "<token>"} y devuelve un nuevo access. Un refresh
    # inválido o expirado responde 401.
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Módulos provisionales: cada rol del personal accede solo al suyo.
    path("modulo-sede/", ModuloSedeView.as_view(), name="modulo-sede"),
    path("modulo-cocina/", ModuloCocinaView.as_view(), name="modulo-cocina"),
    path(
        "modulo-repartidor/",
        ModuloRepartidorView.as_view(),
        name="modulo-repartidor",
    ),
]
