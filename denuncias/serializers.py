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
            "direccion_textual",
            "estado",
            "estado_display",
            "fecha_creacion",
            "imagen",
            "latitud",
            "longitud",
        ]
        read_only_fields = ["id", "fecha_creacion", "estado"]
