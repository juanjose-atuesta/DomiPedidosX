"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticación JWT (login y refresh) - Esto usa auth_urls.py
    path("api/auth/", include("apps.usuarios.auth_urls")),
    # Tus endpoints y los de los demás en usuarios
    path("api/usuarios/", include("apps.usuarios.urls")),
    # Gestión de sedes y sus horarios de atención
    path("api/sedes/", include("apps.sedes.urls")),
    # Catálogo del menú: categorías, productos y grupos de opciones
    path("api/menu/", include("apps.menu.urls")),
    # Promociones con vigencia y cupo diario
    path("api/promociones/", include("apps.promociones.urls")),
    # Disponibilidad e inventario por sede
    path("api/inventario/", include("apps.inventario.urls")),
    # Creación y confirmación de pedidos con descuento de inventario
    path("api/pedidos/", include("apps.pedidos.urls")),
]
