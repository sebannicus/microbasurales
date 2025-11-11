"""Configuración del panel de administración para usuarios."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Usuario


class UsuarioCreationForm(UserCreationForm):
    """Formulario de creación que expone los campos personalizados."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            "username",
            "email",
            "rol",
            "telefono",
            "direccion",
        )


class UsuarioChangeForm(UserChangeForm):
    """Formulario de edición con los campos adicionales del modelo."""

    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = UserChangeForm.Meta.fields + (
            "rol",
            "telefono",
            "direccion",
        )


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin personalizado para gestionar usuarios y roles."""

    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario

    list_display = (
        "username",
        "email",
        "rol",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = (
        "rol",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Información adicional",
            {"fields": ("rol", "telefono", "direccion")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "rol",
                    "telefono",
                    "direccion",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
