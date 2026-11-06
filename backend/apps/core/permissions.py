from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.sedes.models import Sede, SedeUsuario
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


def usuario_opera_en_sede(user, sede):
    """Indica si el usuario trabaja en una sede de su negocio.

    `sede` puede ser una instancia de Sede, su id o None (recurso de todo el
    negocio). El admin opera en todas las sedes de su negocio; el resto solo en
    las asignadas en SedeUsuario y nunca sobre recursos de todo el negocio. Sin
    negocio no se opera en ninguna. El rol lo valida cada vista.
    """
    if not user.is_authenticated or not user.is_active or not user.negocio_id:
        return False
    if user.rol == Rol.ADMIN:
        if sede is None:
            return True
        return Sede.objects.filter(
            pk=getattr(sede, "pk", sede), negocio_id=user.negocio_id
        ).exists()
    if sede is None:
        return False
    return SedeUsuario.objects.filter(
        usuario=user, sede=sede, sede__negocio_id=user.negocio_id
    ).exists()


def usuario_puede_gestionar_sede(user, sede):
    """Indica si el usuario puede gestionar el catálogo operativo de una sede.

    Solo admin y operador gestionan inventario y promociones.
    """
    if user.rol not in (Rol.ADMIN, Rol.OPERADOR):
        return False
    return usuario_opera_en_sede(user, sede)


def exigir_negocio(user):
    """Devuelve el negocio del usuario; sin negocio no puede gestionar nada (403)."""
    if not user.negocio_id:
        raise PermissionDenied("Tu cuenta no pertenece a ningún negocio.")
    return user.negocio


def exigir_gestion_sede(user, sede):
    """Lanza 403 si el usuario no puede gestionar la sede indicada."""
    if not usuario_puede_gestionar_sede(user, sede):
        raise PermissionDenied("No tienes permiso para gestionar esta sede.")


def exigir_operacion_sede(user, sede):
    """Lanza 403 si el usuario no trabaja en la sede indicada."""
    if not usuario_opera_en_sede(user, sede):
        raise PermissionDenied("No tienes permiso para operar en esta sede.")


# Matriz de ejemplo (cada vista declara explícitamente sus roles; el admin NO
# tiene acceso implícito y debe incluirse cuando corresponda):
#
#   sedes ....................... EsAdmin
#   tablero de cocina ........... EsCocina | EsOperador
#   pedidos del repartidor ...... EsRepartidor
#   catálogo / pedidos cliente .. EsCliente
#   reportes .................... EsAdmin | EsOperador
