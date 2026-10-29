# Backend (Django)

API REST con Django REST Framework. Autenticación con JWT.

## Qué hay aquí

- `config/` -> proyecto Django (settings, urls, asgi/wsgi). Se crea con `django-admin startproject config .`
- `apps/` -> una app por dominio. Ver tabla en el README principal.
- `requirements/` -> `base.txt`, `dev.txt`, `prod.txt`
- `.env.example` -> variables de entorno de ejemplo (copiar a `.env`, que NO se sube a Git)
- `pytest.ini` -> configuración de pruebas

## Convenciones

- Los modelos viven en `models.py`; las reglas de negocio (capacidad, cupos, cálculo de
  tiempos, precios) van en `services.py`, no en las vistas.
- Los permisos por rol (cliente, operador, cocina, repartidor, admin) se definen en
  `apps/core/permissions.py` y se reutilizan en las vistas.
- Operaciones que modifican varias tablas (crear pedido, descontar stock, registrar
  historial) se hacen dentro de `transaction.atomic()`.
- Cada app lleva sus pruebas en `tests/`. Ejecutar todas con `pytest`.

## Variables de entorno (`.env`)

Ver `.env.example`. Para usar Supabase, reemplazar `DATABASE_URL` por la cadena de
conexión del proyecto (preferir el pooler en **modo sesión**, puerto 5432).

## Seguridad en Supabase (RLS)

Las tablas que crea Django quedan en el esquema `public`, expuesto por la API de Supabase.
Después de migrar, ejecutar una vez en el SQL Editor de Supabase (y repetir si se agregan tablas):

```sql
DO $$
DECLARE t RECORD;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$;
```

Django se conecta con el rol `postgres`, que ignora RLS, así que no afecta al backend.
