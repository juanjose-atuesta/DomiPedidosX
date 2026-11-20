import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0002_asignar_datos_existentes"),
        ("menu", "0002_negocio_opcional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="categoria",
            name="negocio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="negocios.negocio",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="negocio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="negocios.negocio",
            ),
        ),
    ]
