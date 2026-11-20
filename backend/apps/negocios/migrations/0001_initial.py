import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Negocio",
            fields=[
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                ("descripcion", models.TextField(blank=True)),
                ("logo_url", models.URLField(blank=True)),
                ("activo", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "negocio",
                "verbose_name_plural": "negocios",
                "ordering": ["nombre"],
            },
        ),
    ]
