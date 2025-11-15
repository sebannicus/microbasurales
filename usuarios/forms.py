from django import forms
from django.contrib.auth import get_user_model
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
            css_class = "register-input"
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} {css_class}".strip()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(self.error_messages["password_mismatch"], code="password_mismatch")
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        usuario.rol = Usuario.Roles.CIUDADANO
        if commit:
            usuario.save()
        return usuario
