from django.urls import path

from .views import (
    CategoriaDetailView,
    CategoriaListCreateView,
    ProductoDetailView,
    ProductoListCreateView,
    ProductoOpcionesView,
)

urlpatterns = [
    path(
        "categorias/",
        CategoriaListCreateView.as_view(),
        name="categoria_list_create",
    ),
    path(
        "categorias/<uuid:pk>/",
        CategoriaDetailView.as_view(),
        name="categoria_detail",
    ),
    path(
        "productos/",
        ProductoListCreateView.as_view(),
        name="producto_list_create",
    ),
    path(
        "productos/<uuid:pk>/",
        ProductoDetailView.as_view(),
        name="producto_detail",
    ),
    path(
        "productos/<uuid:pk>/opciones/",
        ProductoOpcionesView.as_view(),
        name="producto_opciones",
    ),
]
