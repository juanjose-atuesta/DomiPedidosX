from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    # Recibe {"refresh": "<token>"} y devuelve un nuevo access. Un refresh
    # inválido o expirado responde 401.
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
