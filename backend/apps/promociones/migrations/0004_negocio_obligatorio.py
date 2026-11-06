import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0002_asignar_datos_existentes"),
        ("promociones", "0003_negocio_opcional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="promocion",
            name="negocio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="promociones",
                to="negocios.negocio",
            ),
        ),
        migrations.AlterField(
            model_name="promocion",
            name="codigo",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddConstraint(
            model_name="promocion",
            constraint=models.UniqueConstraint(
                fields=("negocio", "codigo"), name="uq_promo_codigo_por_negocio"
            ),
        ),
    ]
