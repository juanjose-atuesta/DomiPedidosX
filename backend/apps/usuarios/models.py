from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q

from apps.core.models import ModeloUUID


class Rol(models.TextChoices):
    CLIENTE = "cliente", "Cliente"
    OPERADOR = "operador", "Operador de sede"
    COCINA = "cocina", "Cocina"
    REPARTIDOR = "repartidor", "Repartidor"
    ADMIN = "admin", "Administrador"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email).lower()
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)  # guarda el hash, nunca el texto plano
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("rol", Rol.CLIENTE)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("rol", Rol.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._crear(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, ModeloUUID):
    """Usuario del sistema. Se identifica con el email; el rol define sus permisos."""

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    telefono = models.CharField(max_length=20)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)
    # is_active = False equivale a "desactivar" al usuario (no se borra)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # acceso al admin de Django

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido", "telefono"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    def __str__(self):
        return f"{self.nombre_completo} ({self.rol})"


class Direccion(ModeloUUID):
    """Direcciones de entrega guardadas de un cliente (georreferenciadas)."""

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="direcciones"
    )
    alias = models.CharField(max_length=50)  # 'Casa', 'Trabajo'
    direccion_texto = models.TextField()
    detalles = models.TextField(blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=8)
    longitud = models.DecimalField(max_digits=11, decimal_places=8)
    es_principal = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)  # borrado lógico

    class Meta:
        verbose_name = "dirección"
        verbose_name_plural = "direcciones"
        constraints = [
            # una sola dirección principal activa por cliente
            models.UniqueConstraint(
                fields=["cliente"],
                condition=Q(es_principal=True, activa=True),
                name="uq_direccion_principal_por_cliente",
            ),
        ]

    def __str__(self):
        return f"{self.alias}: {self.direccion_texto}"


class PerfilRepartidor(models.Model):
    """Datos propios de un repartidor: disponibilidad y ubicación aproximada."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="perfil_repartidor",
    )
    disponible = models.BooleanField(default=False)
    latitud = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitud = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    ubicacion_actualizada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "perfil de repartidor"
        verbose_name_plural = "perfiles de repartidor"

    def __str__(self):
        return f"Perfil de {self.usuario}"
