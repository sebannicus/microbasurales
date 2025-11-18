"""Permisos personalizados para el módulo de denuncias."""

from rest_framework import permissions

from .models import Denuncia


class IsFuncionarioMunicipal(permissions.BasePermission):
    """Permite el acceso a personal autorizado para gestionar denuncias."""

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        puede_gestionar = getattr(user, "puede_gestionar_denuncias", None)

        if callable(puede_gestionar):
            puede_gestionar = puede_gestionar()

        if puede_gestionar is None:
            puede_gestionar = getattr(user, "es_funcionario_municipal", False)

        return bool(puede_gestionar)


class PuedeEditarDenunciasFinalizadas(permissions.BasePermission):
    """Restringe la edición de denuncias finalizadas a administradores."""

    message = (
        "Solo cuentas administradoras pueden modificar una denuncia finalizada."
    )

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Denuncia):
            return True

        if obj.estado != Denuncia.EstadoDenuncia.FINALIZADO:
            return True

        return bool(getattr(request.user, "es_administrador", False))
