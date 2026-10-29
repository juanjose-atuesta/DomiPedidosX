# DomiPedidosX

Sistema web de gestión de pedidos y domicilios para restaurantes.
Proyecto del curso **Desarrollo de Software I** (Universidad del Valle, 2026-II).

- **Backend:** Django + Django REST Framework + JWT (carpeta `backend/`)
- **Frontend:** React + Vite (carpeta `frontend/`)
- **Base de datos:** SQLite en local, PostgreSQL (Supabase) en el entorno desplegado
- **Metodología:** Scrum, sprints de 2 semanas

---

## 1. Estructura del repositorio y qué va en cada parte

```
domipedidosx/
├── README.md              <- este archivo
├── .gitignore
├── .github/               <- plantillas y automatizaciones de GitHub
├── docs/                  <- toda la documentación del proyecto
├── backend/               <- API en Django
└── frontend/              <- interfaz en React
```

### `.github/`
Plantilla de Pull Request (`PULL_REQUEST_TEMPLATE.md`) y, más adelante, workflows de
GitHub Actions (por ejemplo, correr las pruebas en cada PR).

### `docs/`
Todo lo que se evalúa como documentación. Ver `docs/README.md` para el detalle.

| Carpeta | Contenido |
|---|---|
| `docs/sprint-0/` | Conformación del equipo, roles, acuerdos, actividades del sprint cero |
| `docs/backlog/` | Product Backlog (mín. 20 historias de usuario), criterios de aceptación, estimaciones (Planning Poker), plan del proyecto, Definition of Done |
| `docs/diseno/` | Enlaces a Figma, diagrama entidad-relación, diagrama de arquitectura |
| `docs/api/` | Documentación de los endpoints (Swagger exportado o colección de Postman) |
| `docs/pruebas/` | Documento de casos de prueba y sus resultados |
| `docs/manuales/` | Manual de instalación, manual de usuario (por actor) y manual del desarrollador |

### `backend/`
API REST en Django. Ver `backend/README.md`.

| Parte | Contenido |
|---|---|
| `config/` | El proyecto Django: `settings.py`, `urls.py`, `asgi.py`, `wsgi.py` (se genera con `django-admin startproject`) |
| `apps/` | Una app de Django por dominio del negocio (ver abajo) |
| `requirements/` | Dependencias: `base.txt` (todos), `dev.txt` (pruebas), `prod.txt` (despliegue) |
| `.env.example` | Plantilla de variables de entorno. El `.env` real NO se sube a Git |
| `pytest.ini` | Configuración de las pruebas |

Apps de `backend/apps/`:

| App | Responsabilidad |
|---|---|
| `core` | Configuración global, permisos base por rol, utilidades compartidas |
| `usuarios` | Modelo de usuario, roles, registro, login JWT, recuperación de contraseña, direcciones, perfil de repartidor |
| `sedes` | Sedes, horarios de atención, feriados |
| `menu` | Categorías, productos, combos, opciones (tamaños, adiciones, ingredientes excluibles) |
| `inventario` | Stock por sede, bloqueo de agotados, alertas de stock mínimo |
| `cobertura` | Zonas de cobertura (tarifas, tiempos, pedido mínimo) y topes de capacidad por franja |
| `pedidos` | Pedidos, detalle, historial de estados, tablero de cocina, cancelaciones |
| `repartos` | Asignación manual o automática de repartidores |
| `promociones` | Promociones y combos con vigencia y cupo máximo diario |
| `notificaciones` | Correos (tareas asíncronas) y alertas al operador/administrador |
| `reportes` | Reportes y estadísticas del dashboard (sin modelos propios, solo consultas) |

Cada app tendrá: `models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`
(lógica de negocio) y `tests/`.

### `frontend/`
Interfaz en React. Ver `frontend/README.md`.

| Carpeta (`src/`) | Contenido |
|---|---|
| `api/` | Cliente Axios y funciones que llaman al backend, agrupadas por módulo |
| `routes/` | Definición de rutas y protección por rol |
| `context/` | Estado global: sesión del usuario, carrito de compras |
| `hooks/` | Hooks personalizados reutilizables |
| `components/` | Componentes reutilizables (botones, tablas, modales, formularios) |
| `layouts/` | Estructuras de página por tipo de usuario (cliente, operador, admin) |
| `pages/cliente/` | Menú, carrito, confirmación de pedido, seguimiento, perfil e historial |
| `pages/operador/` | Pedidos entrantes, creación de pedidos por teléfono/mostrador, menú e inventario de la sede |
| `pages/cocina/` | Tablero kanban de preparación |
| `pages/repartidor/` | Pedidos asignados y registro de entrega |
| `pages/admin/` | Dashboard, reportes, sedes, zonas, reglas de negocio |
| `utils/` | Funciones auxiliares (formato de moneda, fechas, validaciones) |
| `assets/` | Imágenes y recursos estáticos |

---

## 2. Primeros pasos

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
cp .env.example .env               # y editar los valores

# Solo la PRIMERA vez (una persona del equipo, luego se sube a Git):
django-admin startproject config .
for app in core usuarios sedes menu inventario cobertura pedidos repartos promociones notificaciones reportes; do
  python manage.py startapp $app apps/$app
  sed -i -E "s/name = (['\"])$app(['\"])/name = \1apps.$app\2/" apps/$app/apps.py
done
```

> **Importante (hacerlo ANTES de la primera migración):** definir el modelo de usuario
> propio en `apps/usuarios/models.py` (heredando de `AbstractUser`, con el campo `rol`)
> y poner `AUTH_USER_MODEL = "usuarios.User"` en `settings.py`. Cambiarlo después de migrar
> es muy doloroso.

Después de que el proyecto ya existe en Git, los demás integrantes solo hacen:

```bash
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm create vite@latest . -- --template react   # elegir "Ignore files and continue"
npm install
cp .env.example .env
npm run dev
```

---

## 3. Base de datos: cómo trabajamos

| Entorno | Base de datos | Cómo se configura |
|---|---|---|
| Desarrollo local (cada integrante) | SQLite | `DATABASE_URL=sqlite:///db.sqlite3` en `backend/.env` |
| Pruebas automáticas (`pytest`) | SQLite en memoria | Automático con `pytest-django` |
| Desplegado / compartido | PostgreSQL en Supabase | `DATABASE_URL` con la cadena de Supabase |

Reglas:

1. **Las migraciones se suben a Git** (`apps/*/migrations/`). Nadie edita tablas a mano en Supabase.
2. **Una sola persona (o el despliegue) corre `migrate` contra Supabase.** Si varios lo
   hacen a la vez con migraciones distintas, la base queda inconsistente.
3. Si dos personas crean migraciones en la misma app al mismo tiempo, se resuelve con
   `python manage.py makemigrations --merge` antes de unir las ramas.
4. Después de migrar en Supabase, activar RLS en las tablas (ver `backend/README.md`).
5. **Nunca** subir `.env` ni contraseñas al repositorio.

---

## 4. Flujo de trabajo con Git

- Ramas: `main` (estable, entregas) / `develop` (integración) / `feature/<descripcion>`.
- Nadie hace push directo a `main` ni a `develop`: siempre Pull Request con al menos una revisión.
- Mensajes de commit descriptivos, por ejemplo: `feat(pedidos): crear pedido desde el carrito`.
- Los commits y las ramas deben poder rastrearse por sprint.

## 5. Equipo y proceso

Roles Scrum (Product Owner, Scrum Master, Development Team), ceremonias y acuerdos:
ver `docs/sprint-0/`.
