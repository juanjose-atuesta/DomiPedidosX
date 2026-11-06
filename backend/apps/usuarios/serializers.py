from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

from apps.sedes.models import Sede
from .models import User, Direccion, Rol
from .services import ROLES_OPERATIVOS, ROLES_PERSONAL


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
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            # Solo quien conoce la clave puede saber que la cuenta está
            # desactivada; en cualquier otro caso el mensaje es el genérico.
            inactivo = User.objects.filter(email=email, is_active=False).first()
            if inactivo and inactivo.check_password(attrs["password"]):
                raise AuthenticationFailed(
                    "Cuenta desactivada", "cuenta_desactivada"
                )
            raise

        data["user"] = UsuarioSerializer(self.user).data
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    sedes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nombre", "apellido", "email", "telefono", "rol", "sedes")
        read_only_fields = fields

    def get_sedes(self, obj):
        # Sedes activas donde trabaja; define el alcance en las pantallas de personal.
        return [
            {"id": str(sede_usuario.sede_id), "nombre": sede_usuario.sede.nombre}
            for sede_usuario in obj.sedes_asignadas.select_related("sede").filter(
                sede__activa=True
            )
        ]


class RegistroPersonalSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True)
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
            rol=data.get("rol", ""),
        )
        try:
            password_validation.validate_password(password, usuario)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

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

    class Meta:
        model = User
        fields = ("id", "nombre", "apellido", "email", "telefono", "rol", "sedes")
        read_only_fields = fields

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
