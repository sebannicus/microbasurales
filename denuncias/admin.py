from django.contrib import admin

from .models import Denuncia


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
