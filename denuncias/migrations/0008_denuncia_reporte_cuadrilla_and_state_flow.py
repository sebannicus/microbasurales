from django.db import migrations, models


ESTADO_CHOICES = [
    ("pendiente", "Pendiente"),
    ("en_gestion", "En gestión"),
    ("realizado", "Operativo realizado"),
    ("finalizado", "Finalizado"),
]


def normalizar_estados(apps, schema_editor):
    Denuncia = apps.get_model("denuncias", "Denuncia")
    DenunciaNotificacion = apps.get_model("denuncias", "DenunciaNotificacion")

    Denuncia.objects.filter(estado="en_proceso").update(estado="en_gestion")
    Denuncia.objects.filter(estado="resuelta").update(estado="finalizado")

    DenunciaNotificacion.objects.filter(estado_nuevo="en_proceso").update(
        estado_nuevo="en_gestion"
    )
    DenunciaNotificacion.objects.filter(estado_nuevo="resuelta").update(
        estado_nuevo="finalizado"
    )


def revertir_normalizacion(apps, schema_editor):
    Denuncia = apps.get_model("denuncias", "Denuncia")
    DenunciaNotificacion = apps.get_model("denuncias", "DenunciaNotificacion")

    Denuncia.objects.filter(estado="en_gestion").update(estado="en_proceso")
    Denuncia.objects.filter(estado="finalizado").update(estado="resuelta")

    DenunciaNotificacion.objects.filter(estado_nuevo="en_gestion").update(
        estado_nuevo="en_proceso"
    )
    DenunciaNotificacion.objects.filter(estado_nuevo="finalizado").update(
        estado_nuevo="resuelta"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("denuncias", "0007_ensure_denuncia_notificacion_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="denuncia",
            name="reporte_cuadrilla",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Resumen o comprobante entregado por la cuadrilla municipal.",
            ),
        ),
        migrations.AlterField(
            model_name="denuncia",
            name="estado",
            field=models.CharField(
                choices=ESTADO_CHOICES,
                default="pendiente",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="denuncianotificacion",
            name="estado_nuevo",
            field=models.CharField(
                choices=ESTADO_CHOICES,
                max_length=20,
            ),
        ),
        migrations.RunPython(normalizar_estados, revertir_normalizacion),
    ]
