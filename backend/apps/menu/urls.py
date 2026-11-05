from django.urls import path

from .views import (
    CategoriaDetailView,
    CategoriaListCreateView,
    ComboDetailView,
    ComboListCreateView,
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
    path(
        "combos/",
        ComboListCreateView.as_view(),
        name="combo_list_create",
    ),
    path(
        "combos/<uuid:pk>/",
        ComboDetailView.as_view(),
        name="combo_detail",
    ),
]
