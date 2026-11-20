from django.db import migrations


def asignar_negocio_principal(apps, schema_editor):
    """Los datos anteriores al modelo multi-negocio quedan en un solo negocio."""
    modelos = [
        apps.get_model("sedes", "Sede"),
        apps.get_model("menu", "Categoria"),
        apps.get_model("menu", "Producto"),
        apps.get_model("promociones", "Promocion"),
    ]
    personal = apps.get_model("usuarios", "User").objects.exclude(rol="cliente")

    if not personal.exists() and not any(m.objects.exists() for m in modelos):
        return

    negocio = apps.get_model("negocios", "Negocio").objects.create(
        nombre="Negocio principal"
    )
    for modelo in modelos:
        modelo.objects.update(negocio=negocio)
    personal.update(negocio=negocio)


class Migration(migrations.Migration):
    dependencies = [
        ("negocios", "0001_initial"),
        ("sedes", "0003_negocio_opcional"),
        ("menu", "0002_negocio_opcional"),
        ("promociones", "0003_negocio_opcional"),
        ("usuarios", "0002_user_negocio"),
    ]

    operations = [
        migrations.RunPython(asignar_negocio_principal, migrations.RunPython.noop),
    ]
