from django.urls import path

from .views import (
    FeriadoDetailView,
    FeriadoListCreateView,
    SedeDetailView,
    SedeListCreateView,
    SedeReactivarView,
)

urlpatterns = [
    path("", SedeListCreateView.as_view(), name="sede_list_create"),
    path("feriados/", FeriadoListCreateView.as_view(), name="feriado_list_create"),
    path("feriados/<int:pk>/", FeriadoDetailView.as_view(), name="feriado_detail"),
    path("<uuid:pk>/", SedeDetailView.as_view(), name="sede_detail"),
    path(
        "<uuid:pk>/reactivar/",
        SedeReactivarView.as_view(),
        name="sede_reactivar",
    ),
]
