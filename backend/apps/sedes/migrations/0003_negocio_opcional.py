import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0001_initial"),
        ("sedes", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sede",
            name="negocio",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sedes",
                to="negocios.negocio",
            ),
        ),
    ]
