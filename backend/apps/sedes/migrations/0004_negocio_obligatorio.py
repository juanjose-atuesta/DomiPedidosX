import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0002_asignar_datos_existentes"),
        ("sedes", "0003_negocio_opcional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sede",
            name="negocio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sedes",
                to="negocios.negocio",
            ),
        ),
    ]
