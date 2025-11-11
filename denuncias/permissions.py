"""Permisos personalizados para el módulo de denuncias."""

from rest_framework import permissions


class IsFuncionarioMunicipal(permissions.BasePermission):
    """Permite el acceso solo a funcionarios municipales."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "es_funcionario_municipal", False))
