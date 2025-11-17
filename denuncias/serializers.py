import logging

from django.db import OperationalError, ProgrammingError
from rest_framework import serializers

from .models import Denuncia, DenunciaNotificacion, EstadoDenuncia


logger = logging.getLogger(__name__)


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

    def update(self, instance, validated_data):
        estado_anterior = instance.estado
        nuevo_estado = validated_data.get("estado")

        if nuevo_estado and nuevo_estado != estado_anterior:
            self._validar_transicion_estado(
                self.context.get("request"), estado_anterior, nuevo_estado
            )

        instancia_actualizada = super().update(instance, validated_data)

        if nuevo_estado and nuevo_estado != estado_anterior:
            self._crear_notificacion_estado(instancia_actualizada, nuevo_estado)

        return instancia_actualizada

    def _validar_transicion_estado(self, request, estado_anterior, nuevo_estado):
        usuario = getattr(request, "user", None) if request else None

        if not usuario or getattr(usuario, "es_administrador", False):
            return

        transiciones_permitidas = {
            EstadoDenuncia.PENDIENTE: {EstadoDenuncia.EN_PROCESO},
            EstadoDenuncia.EN_PROCESO: {EstadoDenuncia.RESUELTA},
        }

        if nuevo_estado not in transiciones_permitidas.get(estado_anterior, set()):
            raise serializers.ValidationError(
                {
                    "estado": (
                        "Solo puedes avanzar una denuncia de 'Nueva' a 'En proceso'"
                        " o de 'En proceso' a 'Finalizada'."
                    )
                }
            )

    def _crear_notificacion_estado(self, denuncia, nuevo_estado):
        mensaje = self._construir_mensaje_notificacion(denuncia)
        if not mensaje:
            return
        try:
            DenunciaNotificacion.objects.create(
                usuario=denuncia.usuario,
                denuncia=denuncia,
                mensaje=mensaje,
                estado_nuevo=nuevo_estado,
            )
        except (ProgrammingError, OperationalError):
            logger.warning(
                "No se pudo registrar la notificación del cambio de estado; ¿ejecutaste las migraciones?",
                exc_info=True,
            )

    def _construir_mensaje_notificacion(self, denuncia):
        estado_display = denuncia.get_estado_display()
        if not estado_display:
            return ""

        return f"Tu denuncia #{denuncia.id} cambió de estado a \"{estado_display}\"."


class DenunciaCiudadanoSerializer(DenunciaSerializer):
    class Meta(DenunciaSerializer.Meta):
        read_only_fields = DenunciaSerializer.Meta.read_only_fields + [
            "direccion",
            "zona",
            "direccion_textual",
            "latitud",
            "longitud",
        ]

    def update(self, instance, validated_data):
        if instance.estado != EstadoDenuncia.PENDIENTE:
            raise serializers.ValidationError(
                {
                    "estado": "Solo puedes editar denuncias que estén en estado 'Nueva'.",
                }
            )
        return super().update(instance, validated_data)


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
