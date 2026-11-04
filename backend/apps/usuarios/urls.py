from django.urls import path

from .views import RegistroClienteView, MeView

urlpatterns = [
    path("registro/", RegistroClienteView.as_view(), name="registro_cliente"),
    path("me/", MeView.as_view(), name="usuario_me"),
]
