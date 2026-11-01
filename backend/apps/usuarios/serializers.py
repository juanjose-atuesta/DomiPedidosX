"""Serializer del inicio de sesión con JWT."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class LoginSerializer(TokenObtainPairSerializer):
    """Valida email y contraseña y devuelve los tokens JWT con el rol del usuario."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Criterio 1: el rol viaja dentro del token para que el frontend sepa qué módulo mostrar
        token["rol"] = user.rol
        return token

    def validate(self, attrs):
        email = (attrs.get("email") or "").lower()  # los correos se guardan en minúsculas
        password = attrs.get("password")

        user = User.objects.filter(email=email).first()

        # Criterio 4: mismo mensaje si el correo no existe o la contraseña es incorrecta,
        # para no revelar cuál de los dos datos falló
        if user is None or not user.check_password(password):
            raise AuthenticationFailed("Credenciales incorrectas", code="authorization")

        # Criterio 3: se revisa DESPUÉS de validar la clave. Si fuera antes, cualquiera
        # podría descubrir qué correos existen y están desactivados
        if not user.is_active:
            raise AuthenticationFailed("Cuenta desactivada", code="inactive")

        self.user = user  # SimpleJWT espera encontrar el usuario aquí
        refresh = self.get_token(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),  # el id es UUID, se convierte a texto para el JSON
                "nombre": user.nombre_completo,
                "rol": user.rol,
            },
        }