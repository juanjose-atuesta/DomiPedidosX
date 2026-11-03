# apps/usuarios/urls.py
"""Rutas de autenticación."""

from django.urls import path

from .views import (
    LoginView, 
    ModuloCocinaView, 
    ModuloRepartidorView, 
    ModuloSedeView,
    DesactivarUsuarioView, 
    CambiarRolView,       
    DireccionListCreateView 
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("modulo-sede/", ModuloSedeView.as_view(), name="modulo-sede"),
    path("modulo-cocina/", ModuloCocinaView.as_view(), name="modulo-cocina"),
    path("modulo-repartidor/", ModuloRepartidorView.as_view(), name="modulo-repartidor"),

    # rutas HU 1.6-1.9-1.10
    path("usuarios/<uuid:pk>/desactivar/", DesactivarUsuarioView.as_view(), name="desactivar-usuario"),
    path("usuarios/<uuid:pk>/cambiar-rol/", CambiarRolView.as_view(), name="cambiar-rol"),
    path("direcciones/", DireccionListCreateView.as_view(), name="direcciones"),
]

