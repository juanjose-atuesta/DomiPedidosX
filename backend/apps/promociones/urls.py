from django.urls import path

from .views import PromocionDetailView, PromocionListCreateView

urlpatterns = [
    path(
        "",
        PromocionListCreateView.as_view(),
        name="promocion_list_create",
    ),
    path(
        "<uuid:pk>/",
        PromocionDetailView.as_view(),
        name="promocion_detail",
    ),
]
