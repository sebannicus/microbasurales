# Generated manually to incorporar el rol de funcionario municipal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("ciudadano", "Ciudadano"),
                    ("funcionario_municipal", "Funcionario municipal"),
                    ("fiscalizador", "Fiscalizador"),
                    ("administrador", "Administrador"),
                ],
                default="ciudadano",
                max_length=30,
            ),
        ),
    ]
