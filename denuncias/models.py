from django.db import models
from django.conf import settings

class EstadoDenuncia(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PROCESO = 'en_proceso', 'En proceso'
    RESUELTA = 'resuelta', 'Resuelta'


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

    # Ubicación sin GIS, usando latitud y longitud
    latitud = models.FloatField()
    longitud = models.FloatField()

    # Estado de la denuncia
    estado = models.CharField(
        max_length=20,
        choices=EstadoDenuncia.choices,
        default=EstadoDenuncia.PENDIENTE
    )

    # Fecha
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Foto (por ahora ruta local; después la cambiamos a S3)
    imagen = models.ImageField(
        upload_to='denuncias/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Denuncia de {self.usuario} ({self.estado})"
