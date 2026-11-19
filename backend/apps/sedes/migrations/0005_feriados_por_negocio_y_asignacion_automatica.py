"""Sprint 4.

- Sede.asignacion_automatica_repartidor (HU-6.6).
- Feriado pasa a pertenecer a un negocio y a aplicar a varias sedes (HU-8.9):
  se agrega `negocio` (FK) y `sedes` (M2M), se copian los datos del antiguo
  campo `sede` y luego se elimina. Un feriado viejo sin sede no tenía dueño y
  se descarta.
"""

import django.db.models.deletion
from django.db import migrations, models


def copiar_sede_a_negocio(apps, schema_editor):
    Feriado = apps.get_model("sedes", "Feriado")
    for feriado in Feriado.objects.all():
        if feriado.sede_id is None:
            feriado.delete()
            continue
        feriado.negocio_id = feriado.sede.negocio_id
        feriado.save(update_fields=["negocio"])
        feriado.sedes.add(feriado.sede_id)


class Migration(migrations.Migration):

    dependencies = [
        ("negocios", "0002_asignar_datos_existentes"),
        ("sedes", "0004_negocio_obligatorio"),
    ]

    operations = [
        migrations.AddField(
            model_name="sede",
            name="asignacion_automatica_repartidor",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="feriado",
            name="negocio",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feriados",
                to="negocios.negocio",
            ),
        ),
        migrations.AddField(
            model_name="feriado",
            name="sedes",
            field=models.ManyToManyField(
                blank=True, related_name="feriados_m2m", to="sedes.sede"
            ),
        ),
        migrations.RunPython(copiar_sede_a_negocio, migrations.RunPython.noop),
        migrations.RemoveField(model_name="feriado", name="sede"),
        migrations.AlterField(
            model_name="feriado",
            name="sedes",
            field=models.ManyToManyField(
                blank=True, related_name="feriados", to="sedes.sede"
            ),
        ),
        migrations.AlterField(
            model_name="feriado",
            name="negocio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feriados",
                to="negocios.negocio",
            ),
        ),
        migrations.AlterModelOptions(
            name="feriado",
            options={"ordering": ["fecha", "nombre"]},
        ),
    ]
