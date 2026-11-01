# apps/usuarios/urls.py
"""Rutas de autenticación."""

from django.urls import path

from .views import LoginView, ModuloCocinaView, ModuloRepartidorView, ModuloSedeView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("modulo-sede/", ModuloSedeView.as_view(), name="modulo-sede"),
    path("modulo-cocina/", ModuloCocinaView.as_view(), name="modulo-cocina"),
    path("modulo-repartidor/", ModuloRepartidorView.as_view(), name="modulo-repartidor"),
]