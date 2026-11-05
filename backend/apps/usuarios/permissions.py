"""Permisos por rol para restringir cada módulo a su personal."""

from rest_framework.permissions import BasePermission

from .models import Rol


def tiene_rol(*roles):
    """Crea un permiso que solo deja pasar a usuarios autenticados con alguno de los roles dados."""

    class _TieneRol(BasePermission):
        def has_permission(self, request, view):
            usuario = request.user
            # Sin token válido, is_authenticated es False y se responde 401/403
            return bool(usuario and usuario.is_authenticated and usuario.rol in roles)

    return _TieneRol


# Un permiso por cada módulo del personal (HU login, criterio 2)
IsOperador = tiene_rol(Rol.OPERADOR)      # gestión de sede
IsCocina = tiene_rol(Rol.COCINA)          # tablero de cocina
IsRepartidor = tiene_rol(Rol.REPARTIDOR)  # pedidos asignados