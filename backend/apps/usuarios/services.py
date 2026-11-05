from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.sedes.models import Sede, SedeUsuario

from .models import PerfilRepartidor, Rol, User

ROLES_PERSONAL = (Rol.OPERADOR, Rol.COCINA, Rol.REPARTIDOR, Rol.ADMIN)
ROLES_OPERATIVOS = (Rol.OPERADOR, Rol.COCINA, Rol.REPARTIDOR)


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


def crear_usuario_personal(
    *,
    email: str,
    password: str,
    nombre: str,
    apellido: str,
    telefono: str,
    rol: str,
    sedes_ids=None,
) -> User:
    """Crea personal del restaurante y lo asigna a una o varias sedes.

    Los roles operativos (operador, cocina y repartidor) deben tener al menos
    una sede activa. Si el rol es repartidor se crea su PerfilRepartidor.
    """
    with transaction.atomic():
        if rol not in ROLES_PERSONAL:
            raise ValueError(
                "El rol indicado no es válido para registrar personal."
            )

        sedes_ids = list(sedes_ids or [])
        if rol in ROLES_OPERATIVOS and not sedes_ids:
            raise ValueError(
                "Debes asignar al menos una sede para este rol."
            )

        sedes = list(Sede.objects.filter(id__in=sedes_ids, activa=True))
        ids_unicos = {str(sede_id) for sede_id in sedes_ids}
        if sedes_ids and len(sedes) != len(ids_unicos):
            raise ValueError("Una o más sedes no existen o están inactivas.")

        usuario = User.objects.create_user(
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol=rol,
            is_staff=(rol == Rol.ADMIN),
        )

        SedeUsuario.objects.bulk_create(
            [SedeUsuario(usuario=usuario, sede=sede) for sede in sedes]
        )

        if rol == Rol.REPARTIDOR:
            PerfilRepartidor.objects.create(usuario=usuario, disponible=False)

        return usuario


def solicitar_recuperacion_password(*, email: str) -> None:
    """Genera un token de reset y lo envía por correo si el usuario existe.

    Si el correo no está registrado no se lanza ninguna excepción, para no
    revelar qué correos están dados de alta.
    """
    email = email.strip().lower()
    usuario = User.objects.filter(email__iexact=email).first()
    if usuario is None:
        return

    uidb64 = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)

    asunto = "Recuperación de contraseña - DomiPedidosX"
    mensaje = (
        "Recibimos una solicitud para restablecer tu contraseña.\n\n"
        f"uid: {uidb64}\n"
        f"token: {token}\n\n"
        "Si no solicitaste este cambio, ignora este correo."
    )
    send_mail(asunto, mensaje, None, [usuario.email], fail_silently=False)


def confirmar_recuperacion_password(*, uidb64, token, new_password) -> User:
    """Valida el token de recuperación y actualiza la contraseña del usuario."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = User.objects.get(pk=uid)
    except (
        TypeError,
        ValueError,
        OverflowError,
        UnicodeDecodeError,
        DjangoValidationError,
        User.DoesNotExist,
    ):
        raise ValueError("El enlace de recuperación es inválido o expiró.")

    if not default_token_generator.check_token(usuario, token):
        raise ValueError("El enlace de recuperación es inválido o expiró.")

    password_validation.validate_password(new_password, usuario)

    usuario.set_password(new_password)
    usuario.save(update_fields=["password"])
    return usuario


def actualizar_perfil_usuario(
    usuario, *, nombre=None, apellido=None, telefono=None
) -> User:
    """Actualiza únicamente los campos permitidos del perfil del usuario."""
    campos_actualizados = []

    if nombre is not None:
        usuario.nombre = nombre
        campos_actualizados.append("nombre")
    if apellido is not None:
        usuario.apellido = apellido
        campos_actualizados.append("apellido")
    if telefono is not None:
        usuario.telefono = telefono
        campos_actualizados.append("telefono")

    if campos_actualizados:
        usuario.save(update_fields=campos_actualizados)

    return usuario
