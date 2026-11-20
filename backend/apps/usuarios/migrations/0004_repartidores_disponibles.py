"""Sprint 4 (HU-6.5): `disponible` pasa a significar "libre para recibir un
pedido". Los repartidores existentes quedan disponibles, salvo los que ya
llevan un domicilio en curso."""

from django.db import migrations, models


def marcar_disponibles(apps, schema_editor):
    PerfilRepartidor = apps.get_model("usuarios", "PerfilRepartidor")
    Pedido = apps.get_model("pedidos", "Pedido")
    ocupados = Pedido.objects.filter(
        estado__in=["listo_despacho", "en_camino"], repartidor__isnull=False
    ).values("repartidor_id")
    PerfilRepartidor.objects.exclude(usuario_id__in=ocupados).update(disponible=True)
    PerfilRepartidor.objects.filter(usuario_id__in=ocupados).update(disponible=False)


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0003_bloqueo_login_y_activacion"),
        ("pedidos", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perfilrepartidor",
            name="disponible",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(marcar_disponibles, migrations.RunPython.noop),
    ]
