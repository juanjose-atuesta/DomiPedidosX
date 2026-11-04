from rest_framework.permissions import BasePermission

from apps.usuarios.models import Rol


class _RolPermitidoBase(BasePermission):
    """Base para permisos por rol.

    Exige usuario autenticado y activo, y que su rol esté en `roles`.
    La decisión se toma SIEMPRE con request.user.rol (el usuario cargado desde
    la base de datos), nunca con el claim "rol" del token JWT.
    """

    message = "No tienes permiso para realizar esta acción."
    roles = frozenset()

    def has_permission(self, request, view):
        usuario = getattr(request, "user", None)
        if usuario is None or not usuario.is_authenticated:
            return False
        if not usuario.is_active:
            return False
        return usuario.rol in self.roles


def RolPermitido(*roles):
    """Fábrica de clases de permiso para uno o varios roles.

    Uso directo: `permission_classes = [RolPermitido(Rol.COCINA, Rol.OPERADOR)]`.
    También se pueden combinar las clases concretas con el operador `|` de DRF.
    """

    return type(
        "RolPermitido",
        (_RolPermitidoBase,),
        {"roles": frozenset(roles)},
    )


EsCliente = RolPermitido(Rol.CLIENTE)
EsOperador = RolPermitido(Rol.OPERADOR)
EsCocina = RolPermitido(Rol.COCINA)
EsRepartidor = RolPermitido(Rol.REPARTIDOR)
EsAdmin = RolPermitido(Rol.ADMIN)


# Matriz de ejemplo (cada vista declara explícitamente sus roles; el admin NO
# tiene acceso implícito y debe incluirse cuando corresponda):
#
#   sedes ....................... EsAdmin
#   tablero de cocina ........... EsCocina | EsOperador
#   pedidos del repartidor ...... EsRepartidor
#   catálogo / pedidos cliente .. EsCliente
#   reportes .................... EsAdmin | EsOperador
