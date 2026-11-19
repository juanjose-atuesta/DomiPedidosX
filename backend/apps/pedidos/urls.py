from django.urls import path

from .views import (
    PedidoCancelarView,
    PedidoCotizarView,
    PedidoEstadoView,
    PedidoListCreateView,
)

urlpatterns = [
    path("", PedidoListCreateView.as_view(), name="pedido_list_create"),
    path("cotizar/", PedidoCotizarView.as_view(), name="pedido_cotizar"),
    path("<int:pk>/estado/", PedidoEstadoView.as_view(), name="pedido_estado"),
    path("<int:pk>/cancelar/", PedidoCancelarView.as_view(), name="pedido_cancelar"),
]
