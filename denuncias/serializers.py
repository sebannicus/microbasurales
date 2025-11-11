from rest_framework import serializers
from .models import Denuncia

class DenunciaSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Denuncia
        fields = [
            'id',
            'usuario',
            'titulo',
            'descripcion',
            'latitud',
            'longitud',
            'estado',
            'imagen',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'usuario', 'fecha_creacion']


class CrearDenunciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Denuncia
        fields = [
            'titulo',
            'descripcion',
            'latitud',
            'longitud',
            'imagen',
        ]
