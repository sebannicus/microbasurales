from rest_framework import serializers

from .models import Denuncia


class DenunciaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True
    )

    class Meta:
        model = Denuncia
        fields = [
            "id",
            "descripcion",
            "estado",
            "estado_display",
            "fecha_creacion",
            "imagen",
            "latitud",
            "longitud",
        ]
        read_only_fields = ["id", "fecha_creacion", "estado"]


class CrearDenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Denuncia
        fields = [
            "descripcion",
            "latitud",
            "longitud",
            "imagen",
        ]

    def validate(self, attrs):
        latitud = attrs.get("latitud")
        longitud = attrs.get("longitud")

        if latitud is None or longitud is None:
            raise serializers.ValidationError(
                "Debes seleccionar una ubicación en el mapa."
            )

        return attrs
