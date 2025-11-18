"""Formularios utilizados dentro de la app de denuncias."""

from django import forms

from .models import ReporteCuadrilla


class ReporteCuadrillaForm(forms.ModelForm):
    """Formulario que permite a la cuadrilla adjuntar su reporte final."""

    denuncia_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = ReporteCuadrilla
        fields = ["foto_trabajo", "comentario"]
        labels = {
            "foto_trabajo": "Fotografía del trabajo",
            "comentario": "Comentario del jefe de cuadrilla",
        }
        widgets = {
            "foto_trabajo": forms.ClearableFileInput(
                attrs={"accept": "image/*"}
            ),
            "comentario": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe el trabajo realizado por la cuadrilla",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("foto_trabajo", "comentario"):
            css_class = self.fields[field].widget.attrs.get("class", "")
            self.fields[field].widget.attrs["class"] = (
                f"{css_class} form-control".strip()
            )

    def clean_comentario(self):
        comentario = self.cleaned_data.get("comentario", "")
        comentario_limpio = comentario.strip()
        if not comentario_limpio:
            raise forms.ValidationError("El comentario es obligatorio.")
        return comentario_limpio
