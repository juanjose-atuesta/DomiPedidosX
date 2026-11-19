from rest_framework import serializers

from .services import esta_disponible


class RepartidorSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    telefono = serializers.CharField()
    estado = serializers.SerializerMethodField()
    pedidos_hoy = serializers.IntegerField()
    pedidos_en_curso = serializers.IntegerField()

    def get_estado(self, usuario):
        return "disponible" if esta_disponible(usuario) else "ocupado"


class AsignarRepartidorSerializer(serializers.Serializer):
    repartidor_id = serializers.UUIDField()


class ConfiguracionRepartoSerializer(serializers.Serializer):
    asignacion_automatica_repartidor = serializers.BooleanField()
