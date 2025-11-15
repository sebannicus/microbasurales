from django.db import migrations


class Migration(migrations.Migration):
    """Merge branches that introduced denuncia management fields."""

    dependencies = [
        ("denuncias", "0003_denuncia_campos_gestion"),
        ("denuncias", "0003_denuncia_direccion_textual"),
    ]

    operations = []
