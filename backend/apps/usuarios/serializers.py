from rest_framework import serializers
from .models import User


class RegistroClienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmation = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "nombre",
            "apellido",
            "telefono",
            "password",
            "password_confirmacion",
        )

    def validate(self, data):
        if data["password"] != data.pop("password_confirmation"):
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coenciden"}
            )
        return data
