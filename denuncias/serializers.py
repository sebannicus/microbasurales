from rest_framework import serializers
from .models import Denuncia

class DenunciaSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Denuncia
        fields = [
            'id',
            'usuario',
            'descripcion',
            'latitud',
            'longitud',
            'estado',
            'estado_display',
            'imagen',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'usuario', 'fecha_creacion']


class CrearDenunciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Denuncia
        fields = [
            'descripcion',
            'latitud',
            'longitud',
            'imagen',
        ]
