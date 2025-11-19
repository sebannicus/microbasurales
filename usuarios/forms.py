from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

Usuario = get_user_model()


class RegistroUsuarioForm(forms.ModelForm):
    """Formulario de registro para usuarios ciudadanos."""

    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"autofocus": True}),
            "email": forms.EmailInput(),
        }
        labels = {
            "username": _("Nombre de usuario"),
            "email": _("Correo electrónico"),
        }

    error_messages = {
        "password_mismatch": _("Las contraseñas no coinciden."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = "auth-input"
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {css_class}".strip()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(self.error_messages["password_mismatch"], code="password_mismatch")
        return password2

    def save(self, commit=True, rol=None):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        usuario.rol = rol or Usuario.Roles.CIUDADANO
        if commit:
            usuario.save()
        return usuario


class UsuarioAdminUpdateForm(forms.ModelForm):
    """Formulario para que el administrador edite cuentas existentes."""

    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "first_name",
            "telefono",
            "direccion",
            "rol",
            "is_active",
        ]
        labels = {
            "username": _("Nombre de usuario"),
            "email": _("Correo electrónico"),
            "first_name": _("Nombre"),
            "telefono": _("Teléfono"),
            "direccion": _("Dirección"),
            "rol": _("Rol"),
            "is_active": _("Usuario activo"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        roles_permitidos = [
            Usuario.Roles.CIUDADANO,
            Usuario.Roles.FISCALIZADOR,
            Usuario.Roles.JEFE_CUADRILLA,
            Usuario.Roles.ADMINISTRADOR,
        ]

        self.fields["rol"].choices = [
            choice for choice in Usuario.Roles.choices if choice[0] in roles_permitidos
        ]

        for field in self.fields.values():
            widget = field.widget
            existing_classes = widget.attrs.get("class", "")
            base_class = "form-control"
            if isinstance(widget, forms.CheckboxInput):
                base_class = "form-check-input"
            widget.attrs["class"] = f"{existing_classes} {base_class}".strip()


class UserUpdateForm(forms.ModelForm):
    """Permite actualizar la información básica del usuario autenticado."""

    class Meta:
        model = Usuario
        fields = ["email", "telefono", "direccion"]
        labels = {
            "email": _("Correo electrónico"),
            "telefono": _("Teléfono"),
            "direccion": _("Dirección"),
        }
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "usuario@dominio.com"}),
            "telefono": forms.TextInput(attrs={"placeholder": "+54 9 11 5555-5555"}),
            "direccion": forms.TextInput(attrs={"placeholder": "Calle 123, Ciudad"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} form-control".strip()

    def clean_direccion(self):
        """Evita que un usuario elimine una dirección previamente guardada."""

        usuario = self.instance
        nueva_direccion = self.cleaned_data.get("direccion")

        if usuario and usuario.direccion and not nueva_direccion:
            raise forms.ValidationError(
                _("La dirección no puede quedar en blanco una vez registrada.")
            )

        return nueva_direccion

    def clean_telefono(self):
        """Impide eliminar un teléfono ya registrado."""

        usuario = self.instance
        nuevo_telefono = self.cleaned_data.get("telefono")

        if usuario and usuario.telefono and not nuevo_telefono:
            raise forms.ValidationError(
                _("El teléfono no puede quedar en blanco una vez registrado.")
            )

        return nuevo_telefono


class PasswordChangeCustomForm(forms.Form):
    """Formulario personalizado para actualizar la contraseña del usuario."""

    current_password = forms.CharField(
        label=_("Contraseña actual"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label=_("Nueva contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    error_messages = {
        "password_mismatch": _("Las contraseñas nuevas no coinciden."),
        "invalid_current": _("La contraseña actual no es correcta."),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} form-control".strip()

    def clean_current_password(self):
        current_password = self.cleaned_data.get("current_password")
        if not self.user.check_password(current_password):
            raise forms.ValidationError(
                self.error_messages["invalid_current"],
                code="invalid_current",
            )
        return current_password

    def clean_new_password1(self):
        new_password = self.cleaned_data.get("new_password1")
        validate_password(new_password, self.user)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return cleaned_data
