from django.shortcuts import render

# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — inicio de sesión único para todos los roles."""

    serializer_class = LoginSerializer