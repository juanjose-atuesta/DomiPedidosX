import hashlib
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.negocios.models import Negocio
from apps.sedes.models import Sede, SedeUsuario

from .models import Direccion, PerfilRepartidor, Rol, TokenActivacion, User

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


def registrar_negocio(
    *,
    negocio_nombre: str,
    negocio_descripcion: str = "",
    email: str,
    password: str,
    nombre: str,
    apellido: str,
    telefono: str,
) -> User:
    """Crea un negocio y a su administrador responsable, o ninguno de los dos."""
    with transaction.atomic():
        negocio = Negocio.objects.create(
            nombre=negocio_nombre, descripcion=negocio_descripcion
        )
        return User.objects.create_user(
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol=Rol.ADMIN,
            is_staff=True,
            negocio=negocio,
        )


def crear_usuario_personal(
    *,
    negocio,
    email: str,
    nombre: str,
    apellido: str,
    telefono: str,
    rol: str,
    sedes_ids=None,
) -> User:
    """Crea personal de un negocio y lo asigna a una o varias de sus sedes.

    La cuenta nace sin contraseña utilizable: el empleado la define con el
    enlace de activación (válido 24 h) que se le envía por correo.

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

        sedes = list(
            Sede.objects.filter(id__in=sedes_ids, activa=True, negocio=negocio)
        )
        ids_unicos = {str(sede_id) for sede_id in sedes_ids}
        if sedes_ids and len(sedes) != len(ids_unicos):
            raise ValueError("Una o más sedes no existen o están inactivas.")

        usuario = User.objects.create_user(
            email=email,
            password=None,  # contraseña inutilizable hasta activar la cuenta
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol=rol,
            is_staff=(rol == Rol.ADMIN),
            negocio=negocio,
        )

        SedeUsuario.objects.bulk_create(
            [SedeUsuario(usuario=usuario, sede=sede) for sede in sedes]
        )

        if rol == Rol.REPARTIDOR:
            PerfilRepartidor.objects.create(usuario=usuario, disponible=False)

        enviar_enlace_activacion(usuario)
        return usuario


# --- Activación de cuentas del personal (HU-1.4) -----------------------------


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def activacion_pendiente(usuario) -> bool:
    """El personal que aún no ha definido su contraseña."""
    return usuario.rol != Rol.CLIENTE and not usuario.has_usable_password()


def enviar_enlace_activacion(usuario) -> str:
    """Genera un token de un solo uso (24 h) y lo envía por correo.

    Generar uno nuevo invalida los anteriores que no se hayan usado.
    Devuelve el token en claro (solo viaja en el correo).
    """
    token = secrets.token_urlsafe(32)
    with transaction.atomic():
        TokenActivacion.objects.filter(
            usuario=usuario, usado_en__isnull=True
        ).delete()
        TokenActivacion.objects.create(
            usuario=usuario,
            token_hash=_hash_token(token),
            expira_en=timezone.now()
            + timedelta(hours=settings.ACTIVACION_CUENTA_HORAS),
        )

    enlace = f"{settings.FRONTEND_URL}/activar-cuenta/{token}"
    negocio = usuario.negocio.nombre if usuario.negocio_id else "DomiPedidosX"
    mensaje = (
        f"Hola {usuario.nombre},\n\n"
        f"{negocio} creó tu cuenta de {usuario.get_rol_display().lower()} "
        "en DomiPedidosX. Para empezar, define tu contraseña en este enlace:\n\n"
        f"{enlace}\n\n"
        f"El enlace funciona una sola vez y vence en "
        f"{settings.ACTIVACION_CUENTA_HORAS} horas."
    )
    send_mail(
        "Activa tu cuenta - DomiPedidosX",
        mensaje,
        None,
        [usuario.email],
        fail_silently=False,
    )
    return token


MENSAJE_ENLACE_INVALIDO = "El enlace de activación es inválido, ya se usó o expiró."


def obtener_token_activacion(token: str) -> TokenActivacion:
    """Devuelve el token vigente o lanza ValueError."""
    registro = (
        TokenActivacion.objects.select_related("usuario")
        .filter(token_hash=_hash_token(token or ""))
        .first()
    )
    if (
        registro is None
        or registro.usado_en is not None
        or registro.expira_en <= timezone.now()
        or not registro.usuario.is_active
    ):
        raise ValueError(MENSAJE_ENLACE_INVALIDO)
    return registro


def activar_cuenta(*, token: str, password: str) -> User:
    """Define la contraseña del empleado y consume el token."""
    with transaction.atomic():
        registro = obtener_token_activacion(token)
        # Bloquea la fila: dos envíos simultáneos no pueden usar el mismo token.
        registro = TokenActivacion.objects.select_for_update().get(pk=registro.pk)
        if registro.usado_en is not None:
            raise ValueError(MENSAJE_ENLACE_INVALIDO)

        usuario = registro.usuario
        password_validation.validate_password(password, usuario)
        usuario.set_password(password)
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(
            update_fields=["password", "intentos_fallidos", "bloqueado_hasta"]
        )
        registro.usado_en = timezone.now()
        registro.save(update_fields=["usado_en"])
        return usuario


# --- Bloqueo por intentos fallidos (HU-1.2) ----------------------------------


def minutos_restantes_bloqueo(usuario):
    """Minutos que le quedan al bloqueo, o None si la cuenta no está bloqueada."""
    if usuario.bloqueado_hasta is None:
        return None
    restante = usuario.bloqueado_hasta - timezone.now()
    if restante.total_seconds() <= 0:
        return None
    return max(1, -(-int(restante.total_seconds()) // 60))  # redondeo hacia arriba


def registrar_intento_fallido(usuario):
    """Suma un intento fallido; al llegar al máximo bloquea la cuenta.

    Devuelve True si este intento dejó la cuenta bloqueada.
    """
    with transaction.atomic():
        User.objects.filter(pk=usuario.pk).update(
            intentos_fallidos=F("intentos_fallidos") + 1
        )
        usuario = User.objects.select_for_update().get(pk=usuario.pk)
        if usuario.intentos_fallidos < settings.LOGIN_MAX_INTENTOS:
            return False

        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = timezone.now() + timedelta(
            minutes=settings.LOGIN_BLOQUEO_MINUTOS
        )
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])
        return True


def reiniciar_intentos(usuario):
    if usuario.intentos_fallidos or usuario.bloqueado_hasta:
        User.objects.filter(pk=usuario.pk).update(
            intentos_fallidos=0, bloqueado_hasta=None
        )
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None


# --- Clientes ----------------------------------------------------------------


def desactivar_cuenta_cliente(usuario) -> User:
    """El cliente desactiva su cuenta (HU-1.10).

    No se borra nada: sus pedidos (incluidos los que están en curso) y su
    historial se conservan; solo deja de poder iniciar sesión.
    """
    if usuario.rol != Rol.CLIENTE:
        raise ValueError("Solo los clientes pueden desactivar su propia cuenta.")
    usuario.is_active = False
    usuario.save(update_fields=["is_active"])
    return usuario


TELEFONO_CLIENTE = re.compile(r"^\d{10}$")
DOMINIO_SIN_CORREO = "sin-correo.invalid"


def registrar_cliente_rapido(
    *, nombre: str, telefono: str, apellido: str = "", email: str = ""
) -> User:
    """Alta express de un cliente desde el panel del operador (HU-5.9).

    El correo es opcional: sin él se guarda uno interno no entregable (el
    modelo lo exige único). La cuenta no tiene contraseña; si el cliente da
    un correo real puede activarla después con "Recuperar contraseña".
    """
    telefono = (telefono or "").strip()
    if not TELEFONO_CLIENTE.match(telefono):
        raise ValueError("El teléfono debe tener exactamente 10 dígitos.")
    if User.objects.filter(rol=Rol.CLIENTE, telefono=telefono).exists():
        raise ValueError("Ya existe un cliente registrado con ese teléfono.")

    email = (email or "").strip().lower()
    if email and User.objects.filter(email__iexact=email).exists():
        raise ValueError("Ya existe un usuario registrado con ese correo.")

    return User.objects.create_user(
        email=email or f"cliente-{telefono}@{DOMINIO_SIN_CORREO}",
        password=None,
        nombre=nombre.strip(),
        apellido=(apellido or "").strip(),
        telefono=telefono,
        rol=Rol.CLIENTE,
    )


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
    enlace = (
        f"{settings.FRONTEND_URL}/recuperar-contrasena"
        f"?uid={uidb64}&token={token}"
    )
    mensaje = (
        "Recibimos una solicitud para restablecer tu contraseña.\n\n"
        f"Abre este enlace para elegir una nueva (vence en 30 minutos):\n{enlace}\n\n"
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
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.save(update_fields=["password", "intentos_fallidos", "bloqueado_hasta"])
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


def guardar_direccion(cliente, direccion=None, **datos):
    """Crea o actualiza una dirección; si queda como principal, reemplaza a la anterior."""
    with transaction.atomic():
        if datos.get("es_principal"):
            anteriores = Direccion.objects.select_for_update().filter(
                cliente=cliente, activa=True, es_principal=True
            )
            if direccion is not None:
                anteriores = anteriores.exclude(pk=direccion.pk)
            anteriores.update(es_principal=False)

        if direccion is None:
            return Direccion.objects.create(cliente=cliente, **datos)

        for campo, valor in datos.items():
            setattr(direccion, campo, valor)
        direccion.save(update_fields=list(datos))
        return direccion


def desactivar_direccion(direccion):
    """Borrado lógico: los pedidos anteriores conservan su copia de la dirección."""
    direccion.activa = False
    direccion.es_principal = False
    direccion.save(update_fields=["activa", "es_principal"])
    return direccion
