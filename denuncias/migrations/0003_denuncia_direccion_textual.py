from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("denuncias", "0002_remove_denuncia_titulo"),
    ]

    operations = [
        migrations.AddField(
            model_name="denuncia",
            name="direccion_textual",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Dirección descriptiva asociada a la ubicación de la denuncia.",
                max_length=255,
            ),
            preserve_default=False,
        ),
    ]
