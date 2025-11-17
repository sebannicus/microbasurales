from rest_framework import serializers

from .models import Denuncia, EstadoDenuncia


class DenunciaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True
    )
    color = serializers.SerializerMethodField()

    class Meta:
        model = Denuncia
        fields = [
            "id",
            "descripcion",
            "direccion",
            "zona",
            "direccion_textual",
            "estado",
            "estado_display",
            "fecha_creacion",
            "imagen",
            "latitud",
            "longitud",
            "cuadrilla_asignada",
            "color",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado",
            "estado_display",
            "cuadrilla_asignada",
            "color",
        ]

    def get_color(self, obj):
        return EstadoDenuncia.get_color(obj.estado)


class DenunciaAdminSerializer(DenunciaSerializer):
    usuario = serializers.SerializerMethodField()

    class Meta(DenunciaSerializer.Meta):
        fields = DenunciaSerializer.Meta.fields + ["usuario"]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado_display",
            "color",
            "usuario",
        ]

    def get_usuario(self, obj):
        usuario = obj.usuario
        nombre = usuario.get_full_name() or usuario.username
        return {
            "id": usuario.id,
            "nombre": nombre,
            "rol": usuario.rol,
        }

    def validate_estado(self, value):
        if value not in dict(EstadoDenuncia.choices):
            raise serializers.ValidationError("Estado no válido.")
        return value
