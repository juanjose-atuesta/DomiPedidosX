from django.urls import path

from .views import InventarioSedeView

urlpatterns = [
    path(
        "sedes/<uuid:sede_id>/",
        InventarioSedeView.as_view(),
        name="inventario_sede",
    ),
]
