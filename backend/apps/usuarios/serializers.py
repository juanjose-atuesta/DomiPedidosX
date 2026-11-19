from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

from apps.sedes.models import Sede
from .models import User, Direccion, Rol
from .services import (
    ROLES_OPERATIVOS,
    ROLES_PERSONAL,
    activacion_pendiente,
    minutos_restantes_bloqueo,
    registrar_intento_fallido,
    reiniciar_intentos,
)


def mensaje_bloqueo(minutos):
    unidad = "minuto" if minutos == 1 else "minutos"
    return (
        "Tu cuenta está bloqueada temporalmente por demasiados intentos "
        f"fallidos. Intenta de nuevo en {minutos} {unidad}."
    )


class RegistroClienteSerializer(serializers.ModelSerializer):
    # Declarado aparte para que el mensaje de correo repetido sea el de validate_email.
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True)

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

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario registrado con este correo."
            )
        return email

    def validate(self, data):
        password = data.get("password")
        if password != data.pop("password_confirmacion", None):
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden"}
            )

        usuario = User(
            email=data.get("email", ""),
            nombre=data.get("nombre", ""),
            apellido=data.get("apellido", ""),
            telefono=data.get("telefono", ""),
        )
        try:
            password_validation.validate_password(password, usuario)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return data


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Credenciales incorrectas",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["rol"] = user.rol
        return token

    def validate(self, attrs):
        email = attrs[self.username_field].strip().lower()
        attrs[self.username_field] = email
        cuenta = User.objects.filter(email=email).first()

        # Mientras dure el bloqueo ni siquiera la clave correcta abre sesión.
        if cuenta is not None and cuenta.is_active:
            minutos = minutos_restantes_bloqueo(cuenta)
            if minutos:
                raise AuthenticationFailed(
                    mensaje_bloqueo(minutos), "cuenta_bloqueada"
                )

        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            # Solo quien conoce la clave puede saber que la cuenta está
            # desactivada; en cualquier otro caso el mensaje es el genérico.
            if cuenta is not None and not cuenta.is_active:
                if cuenta.check_password(attrs["password"]):
                    raise AuthenticationFailed(
                        "Cuenta desactivada", "cuenta_desactivada"
                    )
                raise
            if cuenta is not None and registrar_intento_fallido(cuenta):
                cuenta.refresh_from_db(fields=["bloqueado_hasta"])
                raise AuthenticationFailed(
                    mensaje_bloqueo(minutos_restantes_bloqueo(cuenta)),
                    "cuenta_bloqueada",
                )
            raise

        reiniciar_intentos(self.user)
        data["user"] = UsuarioSerializer(self.user).data
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    sedes = serializers.SerializerMethodField()
    negocio = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "nombre",
            "apellido",
            "email",
            "telefono",
            "rol",
            "negocio",
            "sedes",
        )
        read_only_fields = fields

    def get_negocio(self, obj):
        if not obj.negocio_id:
            return None
        return {"id": str(obj.negocio_id), "nombre": obj.negocio.nombre}

    def get_sedes(self, obj):
        # Sedes activas donde trabaja; define el alcance en las pantallas de personal.
        return [
            {"id": str(sede_usuario.sede_id), "nombre": sede_usuario.sede.nombre}
            for sede_usuario in obj.sedes_asignadas.select_related("sede").filter(
                sede__activa=True
            )
        ]


class RegistroPersonalSerializer(serializers.ModelSerializer):
    """Alta de personal. No lleva contraseña: el empleado la define con el
    enlace de activación que recibe por correo."""

    email = serializers.EmailField(max_length=150)
    rol = serializers.ChoiceField(choices=ROLES_PERSONAL)
    sedes_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "nombre",
            "apellido",
            "telefono",
            "rol",
            "sedes_ids",
        )

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario registrado con este correo."
            )
        return email

    def validate(self, data):
        sedes_ids = list(dict.fromkeys(data.get("sedes_ids", [])))
        if data.get("rol") in ROLES_OPERATIVOS and not sedes_ids:
            raise serializers.ValidationError(
                {"sedes_ids": "Debes asignar al menos una sede para este rol."}
            )
        if sedes_ids:
            sedes_activas = Sede.objects.filter(id__in=sedes_ids, activa=True).count()
            if sedes_activas != len(sedes_ids):
                raise serializers.ValidationError(
                    {"sedes_ids": ("Una o más sedes no existen o están inactivas.")}
                )

        data["sedes_ids"] = sedes_ids
        return data


class PersonalSerializer(serializers.ModelSerializer):
    sedes = serializers.SerializerMethodField()
    activacion_pendiente = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "nombre",
            "apellido",
            "email",
            "telefono",
            "rol",
            "sedes",
            "activacion_pendiente",
        )
        read_only_fields = fields

    def get_activacion_pendiente(self, obj):
        return activacion_pendiente(obj)

    def get_sedes(self, obj):
        return [
            {"id": str(sede_usuario.sede_id), "nombre": sede_usuario.sede.nombre}
            for sede_usuario in obj.sedes_asignadas.select_related("sede").all()
        ]


class SolicitarPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class ConfirmarPasswordResetSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)


class ActivarCuentaSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data.pop("password_confirmacion"):
            raise serializers.ValidationError(
                {"password_confirmacion": "Las contraseñas no coinciden"}
            )
        return data


class DesactivarCuentaSerializer(serializers.Serializer):
    # Se pide la contraseña para que nadie desactive la cuenta con un
    # dispositivo olvidado con la sesión abierta.
    password = serializers.CharField(write_only=True)


class RegistroRapidoClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100, required=False, allow_blank=True)
    telefono = serializers.RegexField(
        r"^\d{10}$",
        error_messages={"invalid": "El teléfono debe tener exactamente 10 dígitos."},
    )
    email = serializers.EmailField(max_length=150, required=False, allow_blank=True)


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("nombre", "apellido", "telefono")


# --- TUS SERIALIZERS (Camilo) ---

class RolSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=Rol.choices)


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = ['id', 'alias', 'direccion_texto', 'detalles', 'latitud', 'longitud', 'es_principal']


class ClienteBusquedaSerializer(serializers.ModelSerializer):
    """Datos de un cliente para que el personal registre un pedido a su nombre."""

    direcciones = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nombre", "apellido", "email", "telefono", "direcciones")
        read_only_fields = fields

    def get_direcciones(self, obj):
        return DireccionSerializer(obj.direcciones_activas, many=True).data


class RegistroNegocioSerializer(RegistroClienteSerializer):
    """Datos del administrador (como un cliente) más los de su negocio."""

    negocio_nombre = serializers.CharField(max_length=150)
    negocio_descripcion = serializers.CharField(required=False, allow_blank=True)

    class Meta(RegistroClienteSerializer.Meta):
        fields = RegistroClienteSerializer.Meta.fields + (
            "negocio_nombre",
            "negocio_descripcion",
        )
