"""Configuración del panel de administración para las denuncias."""

from django.contrib import admin

from usuarios.models import Usuario

from .models import Denuncia, EstadoDenuncia


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("usuario__username", "descripcion")

    def get_queryset(self, request):
        """Limita la vista del funcionario a denuncias pendientes."""

        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        if isinstance(request.user, Usuario) and request.user.rol == Usuario.Roles.FUNCIONARIO_MUNICIPAL:
            return queryset.filter(estado=EstadoDenuncia.PENDIENTE)

        return queryset
