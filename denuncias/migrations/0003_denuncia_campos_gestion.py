# Generated manually to incorporar campos de gestión y metadatos
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("denuncias", "0002_remove_denuncia_titulo"),
    ]

    operations = [
        migrations.AddField(
            model_name="denuncia",
            name="cuadrilla_asignada",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Equipo responsable de la gestión de la denuncia.",
                max_length=120,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="denuncia",
            name="direccion",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Dirección referencial del evento reportado.",
                max_length=255,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="denuncia",
            name="zona",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Sector o zona operativa asignada por el municipio.",
                max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="denuncia",
            options={"ordering": ("-fecha_creacion",)},
        ),
    ]
