"""Configuración del panel de administración para las denuncias."""

from django.contrib import admin

from usuarios.models import Usuario

from .models import (
    Denuncia,
    DenunciaNotificacion,
    EstadoDenuncia,
    ReporteCuadrilla,
)


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "estado",
        "tiene_reporte",
        "fecha_creacion",
    )
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("usuario__username", "descripcion")
    readonly_fields = ("reporte_cuadrilla",)

    @admin.display(boolean=True, description="Reporte cargado")
    def tiene_reporte(self, obj):
        return getattr(obj, "reporte_cuadrilla", None) is not None

    def get_queryset(self, request):
        """Limita la vista del funcionario a denuncias pendientes."""

        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        if isinstance(request.user, Usuario) and request.user.rol == Usuario.Roles.FUNCIONARIO_MUNICIPAL:
            return queryset.filter(estado=EstadoDenuncia.PENDIENTE)

        return queryset


@admin.register(DenunciaNotificacion)
class DenunciaNotificacionAdmin(admin.ModelAdmin):
    list_display = ("denuncia", "usuario", "estado_nuevo", "leida", "fecha_creacion")
    list_filter = ("estado_nuevo", "leida", "fecha_creacion")
    search_fields = ("denuncia__descripcion", "usuario__username")


@admin.register(ReporteCuadrilla)
class ReporteCuadrillaAdmin(admin.ModelAdmin):
    list_display = ("id", "denuncia", "jefe_cuadrilla", "fecha_reporte")
    search_fields = ("denuncia__descripcion", "jefe_cuadrilla__username")
    autocomplete_fields = ["denuncia", "jefe_cuadrilla"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        denuncia_field = form.base_fields.get("denuncia")
        if denuncia_field:
            queryset = self._denuncias_sin_reporte_queryset()
            if obj and obj.denuncia_id:
                queryset = queryset | Denuncia.objects.filter(pk=obj.denuncia_id)
            denuncia_field.queryset = queryset.distinct()
        return form

    def _denuncias_sin_reporte_queryset(self):
        return Denuncia.objects.filter(reporte_cuadrilla__isnull=True)
