from django.urls import path

from .views import PedidoListCreateView

urlpatterns = [
    path("", PedidoListCreateView.as_view(), name="pedido_list_create"),
]
