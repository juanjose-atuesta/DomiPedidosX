from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.sedes.models import Sede

from .models import User
from .services import ROLES_OPERATIVOS, ROLES_PERSONAL


class RegistroClienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmacion = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # rol, is_staff, is_active e is_superuser no se exponen: si el cliente
        # los envía, DRF los ignora y el usuario queda siempre como cliente.
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
    """Proceso de login:

    1. Recibe "email" y "password".
    2. Normaliza el email (sin espacios y en minúsculas).
    3. TokenObtainPairSerializer valida las credenciales con el backend de
       autenticación de Django. Si el correo no existe, la contraseña es
       incorrecta o el usuario está inactivo, responde 401 con el mismo
       mensaje genérico para no revelar si el correo está registrado.
    4. Genera el par de tokens access/refresh y agrega el rol como claim
       informativo.
    """

    default_error_messages = {
        "no_active_account": "Correo o contraseña incorrectos.",
    }

    # Agrega el claim "rol" al token para que el cliente sepa qué interfaz
    # mostrar. Nota: los permisos NO se deben decidir confiando solo en este
    # claim; el backend siempre debe consultar el usuario autenticado.
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["rol"] = user.rol
        return token

    # Normaliza el email antes de autenticar, de modo que el login funcione
    # aunque el cliente lo envíe con mayúsculas o espacios.
    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().lower()
        return super().validate(attrs)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "nombre", "apellido", "email", "telefono", "rol")
        read_only_fields = fields


class RegistroPersonalSerializer(serializers.ModelSerializer):
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
            sedes_activas = Sede.objects.filter(
                id__in=sedes_ids, activa=True
            ).count()
            if sedes_activas != len(sedes_ids):
                raise serializers.ValidationError(
                    {
                        "sedes_ids": (
                            "Una o más sedes no existen o están inactivas."
                        )
                    }
                )

        data["sedes_ids"] = sedes_ids
        return data


class PersonalSerializer(serializers.ModelSerializer):
    sedes = serializers.SerializerMethodField()

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
        )
        read_only_fields = fields

    def get_sedes(self, obj):
        return [
            {
                "id": str(sede_usuario.sede_id),
                "nombre": sede_usuario.sede.nombre,
            }
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
