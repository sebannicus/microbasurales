from django.db import models
from django.conf import settings

class EstadoDenuncia(models.TextChoices):
    PENDIENTE = "pendiente", "Nueva"
    EN_PROCESO = "en_proceso", "En gestión"
    RESUELTA = "resuelta", "Finalizada"

    COLOR_DEFAULT = "#1d3557"

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


_ESTADO_DENUNCIA_COLOR_MAP = {
    EstadoDenuncia.PENDIENTE: "#d32f2f",
    EstadoDenuncia.EN_PROCESO: "#f57c00",
    EstadoDenuncia.RESUELTA: "#388e3c",
}


class Denuncia(models.Model):
    """
    Modelo principal para una denuncia.
    """
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
