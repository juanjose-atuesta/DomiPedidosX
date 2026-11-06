from django.urls import path

from .views import PedidoEstadoView, PedidoListCreateView

urlpatterns = [
    path("", PedidoListCreateView.as_view(), name="pedido_list_create"),
    path("<int:pk>/estado/", PedidoEstadoView.as_view(), name="pedido_estado"),
]
