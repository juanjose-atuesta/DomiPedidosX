from django.urls import path

from .views import SedeDetailView, SedeListCreateView, SedeReactivarView

urlpatterns = [
    path("", SedeListCreateView.as_view(), name="sede_list_create"),
    path("<uuid:pk>/", SedeDetailView.as_view(), name="sede_detail"),
    path(
        "<uuid:pk>/reactivar/",
        SedeReactivarView.as_view(),
        name="sede_reactivar",
    ),
]
