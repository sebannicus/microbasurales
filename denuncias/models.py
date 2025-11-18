from django.conf import settings
from django.db import models

class EstadoDenuncia(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    EN_GESTION = "en_gestion", "En gestión"
    REALIZADO = "realizado", "Operativo realizado"
    FINALIZADO = "finalizado", "Finalizado"

    @classmethod
    def color_map(cls):
        """Retorna el mapa de colores configurado para cada estado."""

        return _ESTADO_DENUNCIA_COLOR_MAP

    @classmethod
    def get_color(cls, estado):
        """Obtiene el color asociado al estado solicitado."""

        return cls.color_map().get(estado, cls.COLOR_DEFAULT)

    @classmethod
    def as_config(cls):
        """Entrega la configuración serializable de estados y colores."""

        return [
            {"value": value, "label": label, "color": cls.get_color(value)}
            for value, label in cls.choices
        ]


# Este valor se define fuera de la clase para que Django no lo interprete como choice
EstadoDenuncia.COLOR_DEFAULT = "#1d3557"


_ESTADO_DENUNCIA_COLOR_MAP = {
    EstadoDenuncia.PENDIENTE: "#d32f2f",
    EstadoDenuncia.EN_GESTION: "#f57c00",
    EstadoDenuncia.REALIZADO: "#1976d2",
    EstadoDenuncia.FINALIZADO: "#388e3c",
}


class Denuncia(models.Model):
    """
    Modelo principal para una denuncia.
    """
    # Alias al enumerador de estados para mantener compatibilidad con
    # otros módulos que esperan accederlo como `Denuncia.EstadoDenuncia`.
    EstadoDenuncia = EstadoDenuncia

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='denuncias'
    )

    descripcion = models.TextField()

    direccion = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Dirección referencial del evento reportado.",
    )

    zona = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Sector o zona operativa asignada por el municipio.",
    )

    # Dirección legible seleccionada por la persona denunciante
    direccion_textual = models.CharField(
        max_length=255,
        blank=True,
        help_text="Dirección descriptiva asociada a la ubicación de la denuncia.",
    )

    # Ubicación sin GIS, usando latitud y longitud
    latitud = models.FloatField()
    longitud = models.FloatField()

    # Estado de la denuncia
    estado = models.CharField(
        max_length=20,
        choices=EstadoDenuncia.choices,
        default=EstadoDenuncia.PENDIENTE
    )

    cuadrilla_asignada = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Equipo responsable de la gestión de la denuncia.",
    )

    reporte_cuadrilla = models.TextField(
        blank=True,
        default="",
        help_text="Resumen o comprobante entregado por la cuadrilla municipal.",
    )

    # Fecha
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Foto (por ahora ruta local; después la cambiamos a S3)
    imagen = models.ImageField(
        upload_to='denuncias/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ("-fecha_creacion",)

    def __str__(self):
        return f"Denuncia de {self.usuario} ({self.estado})"


class DenunciaNotificacion(models.Model):
    """Notificación simple asociada a los cambios de estado de una denuncia."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones_denuncia",
    )
    denuncia = models.ForeignKey(
        "Denuncia",
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    mensaje = models.CharField(max_length=255)
    estado_nuevo = models.CharField(
        max_length=20,
        choices=EstadoDenuncia.choices,
    )
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-fecha_creacion",)

    def __str__(self):
        return f"Notificación {self.denuncia_id} → {self.get_estado_nuevo_display()}"
