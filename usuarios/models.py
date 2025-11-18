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
        JEFE_CUADRILLA = "jefe_cuadrilla", "Jefe de cuadrilla"
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

    @property
    def es_fiscalizador(self) -> bool:
        """True si el usuario corresponde al rol de fiscalizador."""

        return self.rol == self.Roles.FISCALIZADOR

    @property
    def es_administrador(self) -> bool:
        """True para cuentas administrativas o superusuarios."""

        return self.rol == self.Roles.ADMINISTRADOR or self.is_superuser

    @property
    def es_jefe_cuadrilla(self) -> bool:
        """True para el rol de jefe de cuadrilla."""

        return self.rol == self.Roles.JEFE_CUADRILLA

    @property
    def puede_gestionar_denuncias(self) -> bool:
        """Indica si el usuario puede acceder al panel de denuncias especializado."""

        return self.es_fiscalizador or self.es_administrador

    def __str__(self):
        return f"{self.username} ({self.rol})"
