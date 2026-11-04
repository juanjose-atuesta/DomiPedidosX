from typing import Dict, Any
from django.db import transaction
from .models import User, Rol


def registrar_cliente(
    *, email: str, password: str, nombre: str, apellido: str, telefono: str
) -> User:
    # Registra un usuario nuevo asegurando que su rol por defecto sea cliente
    with transaction.atomic():
        usuario = User.objects.create_user(
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol=Rol.CLIENTE,
        )
        return usuario
