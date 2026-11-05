"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticación JWT (login y refresh)
    path("api/auth/", include("apps.usuarios.auth_urls")),
    # Incluye las urls de la app usuarios bajo el prefijo api/usuarios/
    path("api/usuarios/", include("apps.usuarios.urls")),
    # Gestión de sedes y sus horarios de atención
    path("api/sedes/", include("apps.sedes.urls")),
    # Catálogo del menú: categorías, productos y grupos de opciones
    path("api/menu/", include("apps.menu.urls")),
    # Promociones con vigencia y cupo diario
    path("api/promociones/", include("apps.promociones.urls")),
    # Disponibilidad e inventario por sede
    path("api/inventario/", include("apps.inventario.urls")),
]
