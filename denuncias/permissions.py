"""Permisos personalizados para el módulo de denuncias."""

from rest_framework import permissions


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
