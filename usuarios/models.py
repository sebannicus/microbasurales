from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Modelo de usuario extendido con soporte de roles."""

    class Roles(models.TextChoices):
        CIUDADANO = "ciudadano", "Ciudadano"
        FUNCIONARIO_MUNICIPAL = (
            "funcionario_municipal",
            "Funcionario municipal",
        )
        FISCALIZADOR = "fiscalizador", "Fiscalizador"
        ADMINISTRADOR = "administrador", "Administrador"

    rol = models.CharField(
        max_length=30,
        choices=Roles.choices,
        default=Roles.CIUDADANO,
    )

    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def es_funcionario_municipal(self) -> bool:
        """Indica si el usuario tiene el rol de funcionario municipal."""

        return self.rol == self.Roles.FUNCIONARIO_MUNICIPAL

    def __str__(self):
        return f"{self.username} ({self.rol})"
