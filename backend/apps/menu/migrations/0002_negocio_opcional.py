import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0001_initial"),
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria",
            name="negocio",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="negocios.negocio",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="negocio",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="negocios.negocio",
            ),
        ),
    ]
