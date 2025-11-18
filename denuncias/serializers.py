import logging

from django.db import OperationalError, ProgrammingError
from rest_framework import serializers

from .models import (
    Denuncia,
    DenunciaNotificacion,
    EstadoDenuncia,
    ReporteCuadrilla,
)


logger = logging.getLogger(__name__)


class ReporteCuadrillaSerializer(serializers.ModelSerializer):
    jefe_cuadrilla = serializers.SerializerMethodField()

    class Meta:
        model = ReporteCuadrilla
        fields = [
            "id",
            "comentario",
            "foto_trabajo",
            "fecha_reporte",
            "jefe_cuadrilla",
        ]
        read_only_fields = fields

    def get_jefe_cuadrilla(self, obj):
        jefe = obj.jefe_cuadrilla
        if not jefe:
            return None
        return {
            "id": jefe.id,
            "nombre": jefe.get_full_name() or jefe.username,
        }


class DenunciaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True
    )
    color = serializers.SerializerMethodField()
    reporte_cuadrilla = ReporteCuadrillaSerializer(read_only=True)

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
            "reporte_cuadrilla",
            "color",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado",
            "estado_display",
            "cuadrilla_asignada",
            "reporte_cuadrilla",
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

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        nuevo_estado = attrs.get("estado")

        if not instance or not nuevo_estado or nuevo_estado == instance.estado:
            return attrs

        usuario = self._obtener_usuario()

        if not usuario:
            raise serializers.ValidationError(
                {"estado": "No tienes permisos para modificar este registro."}
            )

        transiciones = self._obtener_transiciones_permitidas(usuario)
        transiciones_desde_estado = transiciones.get(instance.estado, set())

        if nuevo_estado not in transiciones_desde_estado:
            raise serializers.ValidationError(
                {
                    "estado": (
                        "No puedes mover la denuncia al estado solicitado desde su estado actual."
                    )
                }
            )

        if (
            instance.estado == EstadoDenuncia.EN_GESTION
            and nuevo_estado == EstadoDenuncia.REALIZADO
        ):
            reporte = attrs.get("reporte_cuadrilla") or instance.reporte_cuadrilla
            if not reporte:
                raise serializers.ValidationError(
                    {
                        "reporte_cuadrilla": (
                            "Debes adjuntar un reporte de cuadrilla antes de marcar la denuncia como realizada."
                        )
                    }
                )

        return attrs

    def update(self, instance, validated_data):
        estado_anterior = instance.estado
        nuevo_estado = validated_data.get("estado")

        instancia_actualizada = super().update(instance, validated_data)

        if nuevo_estado and nuevo_estado != estado_anterior:
            self._crear_notificacion_estado(instancia_actualizada, nuevo_estado)

        return instancia_actualizada

    def _obtener_usuario(self):
        request = self.context.get("request") if self.context else None
        return getattr(request, "user", None)

    def _obtener_transiciones_permitidas(self, usuario):
        if getattr(usuario, "es_administrador", False):
            return {
                EstadoDenuncia.REALIZADO: {EstadoDenuncia.FINALIZADO},
            }

        if getattr(usuario, "es_fiscalizador", False):
            return {
                EstadoDenuncia.PENDIENTE: {EstadoDenuncia.EN_GESTION},
                EstadoDenuncia.EN_GESTION: {EstadoDenuncia.REALIZADO},
            }

        return {}

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

        if denuncia.estado == EstadoDenuncia.FINALIZADO:
            return (
                f"Tu denuncia #{denuncia.id} ha sido finalizada por el municipio."
            )

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
