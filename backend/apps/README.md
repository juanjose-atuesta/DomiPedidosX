# apps/

Una carpeta por dominio. Para crear una app nueva:

```bash
mkdir apps/nombre
python manage.py startapp nombre apps/nombre
# y en apps/nombre/apps.py poner: name = "apps.nombre"
# y registrarla en INSTALLED_APPS como "apps.nombre"
```

Estructura recomendada dentro de cada app:

```
nombre/
├── models.py        <- tablas
├── serializers.py   <- conversión modelo <-> JSON y validaciones
├── views.py         <- endpoints (ViewSets de DRF)
├── urls.py          <- rutas de la app
├── services.py      <- lógica de negocio
├── admin.py
├── migrations/      <- SE SUBEN a Git
└── tests/
```
