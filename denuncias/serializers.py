import logging

from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from rest_framework import serializers

from .models import (
    Denuncia,
    DenunciaNotificacion,
    EstadoDenuncia,
    HistorialEstado,
    ReporteCuadrilla,
)


logger = logging.getLogger(__name__)
Usuario = get_user_model()


class JefeCuadrillaField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        if not value:
            return None
        return {"id": value.id, "username": value.username}


MOTIVOS_RECHAZO_TEXTOS = {
    "foto_insuficiente": "La denuncia no puede procesarse: evidencia insuficiente (foto poco clara).",
    "no_verificada": "No se logró verificar el microbasural en terreno.",
    "datos_insuficientes": "El reporte no contiene datos suficientes para acudir al lugar.",
    "ya_gestionada": "La denuncia ya está siendo gestionada bajo otro caso activo. (denuncia duplicada)",
}


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
    reporte_cuadrilla = ReporteCuadrillaSerializer(
        read_only=True, allow_null=True
    )
    jefe_cuadrilla_asignado = serializers.SerializerMethodField()

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
            "motivo_rechazo",
            "jefe_cuadrilla_asignado",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "estado",
            "estado_display",
            "cuadrilla_asignada",
            "reporte_cuadrilla",
            "color",
            "motivo_rechazo",
            "jefe_cuadrilla_asignado",
        ]

    def get_color(self, obj):
        return EstadoDenuncia.get_color(obj.estado)

    def get_jefe_cuadrilla_asignado(self, obj):
        jefe = getattr(obj, "jefe_cuadrilla_asignado", None)
        if not jefe:
            return None
        return {"id": jefe.id, "username": jefe.username}


class DenunciaAdminSerializer(DenunciaSerializer):
    usuario = serializers.SerializerMethodField()
    jefe_cuadrilla_asignado = JefeCuadrillaField(
        queryset=Usuario.objects.filter(rol=Usuario.Roles.JEFE_CUADRILLA),
        allow_null=True,
        required=False,
    )

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
        estado_normalizado = EstadoDenuncia.normalize(value)
        if estado_normalizado not in dict(EstadoDenuncia.choices):
            raise serializers.ValidationError("Estado no válido.")
        return estado_normalizado

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        estado_actual = (
            EstadoDenuncia.normalize(instance.estado) if instance else None
        )
        nuevo_estado = attrs.get("estado")
        jefe_enviado = attrs.get("jefe_cuadrilla_asignado", serializers.empty)

        if not instance or not nuevo_estado or nuevo_estado == estado_actual:
            if jefe_enviado is not serializers.empty:
                raise serializers.ValidationError(
                    {
                        "jefe_cuadrilla_asignado": (
                            "Solo puedes asignar un jefe de cuadrilla cuando cambias la denuncia a 'En gestión'."
                        )
                    }
                )
            attrs.pop("motivo_rechazo", None)
            return attrs

        usuario = self._obtener_usuario()

        if not usuario:
            raise serializers.ValidationError(
                {"estado": "No tienes permisos para modificar este registro."}
            )

        if nuevo_estado == EstadoDenuncia.RECHAZADA:
            self._validar_rechazo(usuario, estado_actual, attrs)

        jefe_resultante = (
            instance.jefe_cuadrilla_asignado if jefe_enviado is serializers.empty else jefe_enviado
        )

        if nuevo_estado == EstadoDenuncia.EN_GESTION:
            if not getattr(usuario, "es_fiscalizador", False):
                raise serializers.ValidationError(
                    {
                        "estado": "Solo personal fiscalizador puede mover la denuncia a 'En gestión'."
                    }
                )
            if jefe_resultante is None:
                raise serializers.ValidationError(
                    {
                        "jefe_cuadrilla_asignado": (
                            "Debes seleccionar un jefe de cuadrilla para continuar."
                        )
                    }
                )
        elif jefe_enviado is not serializers.empty:
            raise serializers.ValidationError(
                {
                    "jefe_cuadrilla_asignado": (
                        "Solo puedes asignar un jefe de cuadrilla al cambiar la denuncia a 'En gestión'."
                    )
                }
            )

        transiciones = self._obtener_transiciones_permitidas(usuario)
        transiciones_desde_estado = transiciones.get(estado_actual, set())

        if nuevo_estado not in transiciones_desde_estado:
            raise serializers.ValidationError(
                {
                    "estado": (
                        "No puedes mover la denuncia al estado solicitado desde su estado actual."
                    )
                }
            )

        if (
            estado_actual == EstadoDenuncia.EN_GESTION
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

        if nuevo_estado != EstadoDenuncia.RECHAZADA:
            attrs.pop("motivo_rechazo", None)

        return attrs

    def update(self, instance, validated_data):
        estado_anterior = EstadoDenuncia.normalize(instance.estado)
        nuevo_estado = validated_data.get("estado")

        instancia_actualizada = super().update(instance, validated_data)

        if (
            instancia_actualizada.estado != EstadoDenuncia.RECHAZADA
            and instancia_actualizada.motivo_rechazo
        ):
            instancia_actualizada.motivo_rechazo = None
            instancia_actualizada.save(update_fields=["motivo_rechazo"])

        if nuevo_estado and nuevo_estado != estado_anterior:
            self._crear_notificacion_estado(instancia_actualizada, nuevo_estado)
            self._registrar_historial_estado(
                instancia_actualizada, estado_anterior, nuevo_estado
            )

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
                EstadoDenuncia.PENDIENTE: {
                    EstadoDenuncia.EN_GESTION,
                    EstadoDenuncia.RECHAZADA,
                },
                EstadoDenuncia.EN_GESTION: {
                    EstadoDenuncia.REALIZADO,
                    EstadoDenuncia.RECHAZADA,
                },
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

        if denuncia.estado == EstadoDenuncia.RECHAZADA:
            motivo = denuncia.motivo_rechazo or ""
            motivo_texto = motivo.strip()
            if motivo_texto:
                return f"Tu denuncia ha sido rechazada. Motivo: {motivo_texto}."
            return "Tu denuncia ha sido rechazada."

        return f"Tu denuncia #{denuncia.id} cambió de estado a \"{estado_display}\"."

    def _validar_rechazo(self, usuario, estado_actual, attrs):
        if not getattr(usuario, "es_fiscalizador", False):
            raise serializers.ValidationError(
                {"estado": "Solo personal fiscalizador puede rechazar denuncias."}
            )

        if estado_actual not in {
            EstadoDenuncia.PENDIENTE,
            EstadoDenuncia.EN_GESTION,
        }:
            raise serializers.ValidationError(
                {
                    "estado": (
                        "La denuncia no puede ser rechazada desde su estado actual."
                    )
                }
            )

        motivo_normalizado = self._resolver_motivo_rechazo(attrs.get("motivo_rechazo"))

        if not motivo_normalizado:
            raise serializers.ValidationError(
                {
                    "motivo_rechazo": (
                        "Debes seleccionar un motivo para rechazar la denuncia."
                    )
                }
            )

        attrs["motivo_rechazo"] = motivo_normalizado

    def _resolver_motivo_rechazo(self, valor):
        if valor is None:
            return ""

        texto = str(valor).strip()
        if not texto:
            return ""

        clave = texto.lower()
        if clave == "otro":
            return ""

        return MOTIVOS_RECHAZO_TEXTOS.get(clave, texto)

    def _registrar_historial_estado(self, denuncia, estado_anterior, estado_nuevo):
        responsable = self._obtener_usuario()
        try:
            registro = HistorialEstado.objects.create(
                denuncia=denuncia,
                estado_anterior=estado_anterior or "",
                estado_nuevo=estado_nuevo or "",
                responsable=responsable if getattr(responsable, "is_authenticated", False) else None,
            )
            denuncia.historial.add(registro)
        except (ProgrammingError, OperationalError):
            logger.warning(
                "No se pudo registrar el historial del cambio de estado; ¿ejecutaste las migraciones?",
                exc_info=True,
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
