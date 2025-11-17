from rest_framework import serializers

from .models import Denuncia, DenunciaNotificacion, EstadoDenuncia


class DenunciaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True
    )

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
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado",
            "estado_display",
            "cuadrilla_asignada",
        ]


class DenunciaAdminSerializer(DenunciaSerializer):
    usuario = serializers.SerializerMethodField()
    ESTADO_MENSAJES = {
        EstadoDenuncia.EN_PROCESO: "Tu denuncia \"{descripcion}\" está siendo gestionada por nuestro equipo.",
        EstadoDenuncia.RESUELTA: "Tu denuncia \"{descripcion}\" fue finalizada por el municipio.",
    }

    class Meta(DenunciaSerializer.Meta):
        fields = DenunciaSerializer.Meta.fields + ["usuario"]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado_display",
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

    def update(self, instance, validated_data):
        estado_anterior = instance.estado
        instancia_actualizada = super().update(instance, validated_data)
        nuevo_estado = validated_data.get("estado")

        if nuevo_estado and nuevo_estado != estado_anterior:
            self._crear_notificacion_estado(instancia_actualizada, nuevo_estado)

        return instancia_actualizada

    def _crear_notificacion_estado(self, denuncia, nuevo_estado):
        mensaje_base = self.ESTADO_MENSAJES.get(nuevo_estado)
        if not mensaje_base:
            return

        descripcion = (denuncia.descripcion or "Sin descripción").strip()
        if len(descripcion) > 80:
            descripcion = f"{descripcion[:77]}…"

        mensaje = mensaje_base.format(descripcion=descripcion)
        DenunciaNotificacion.objects.create(
            usuario=denuncia.usuario,
            denuncia=denuncia,
            mensaje=mensaje,
            estado_nuevo=nuevo_estado,
        )


class DenunciaCiudadanoSerializer(DenunciaSerializer):
    class Meta(DenunciaSerializer.Meta):
        read_only_fields = DenunciaSerializer.Meta.read_only_fields + [
            "direccion",
            "zona",
            "direccion_textual",
            "latitud",
            "longitud",
        ]


class NotificacionDenunciaSerializer(serializers.ModelSerializer):
    estado_nuevo_display = serializers.CharField(
        source="get_estado_nuevo_display", read_only=True
    )
    denuncia_descripcion = serializers.CharField(
        source="denuncia.descripcion", read_only=True
    )

    class Meta:
        model = DenunciaNotificacion
        fields = [
            "id",
            "mensaje",
            "leida",
            "fecha_creacion",
            "denuncia",
            "denuncia_descripcion",
            "estado_nuevo",
            "estado_nuevo_display",
        ]
        read_only_fields = [
            "id",
            "mensaje",
            "fecha_creacion",
            "denuncia",
            "denuncia_descripcion",
            "estado_nuevo",
            "estado_nuevo_display",
        ]
        extra_kwargs = {"leida": {"required": False}}
