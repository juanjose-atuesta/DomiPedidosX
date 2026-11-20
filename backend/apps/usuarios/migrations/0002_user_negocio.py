import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0001_initial"),
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="negocio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="usuarios",
                to="negocios.negocio",
            ),
        ),
    ]
