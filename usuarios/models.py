from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Modelo de usuario extendido.
    Usa el sistema de autenticación de Django, pero agrega un campo 'rol'.
    """

    ROLES = [
        ('ciudadano', 'Ciudadano'),
        ('fiscalizador', 'Fiscalizador'),
        ('administrador', 'Administrador'),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='ciudadano'
    )

    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.rol})"
