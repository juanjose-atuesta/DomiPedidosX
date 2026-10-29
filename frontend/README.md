# Frontend (React + Vite)

Interfaz web responsive para los cinco actores: cliente, operador de sede, cocina,
repartidor y administrador.

## Qué hay aquí

Ver la tabla de `src/` en el README principal. Resumen:

- `src/api/` -> llamadas al backend (Axios)
- `src/routes/` -> rutas y protección por rol
- `src/context/` -> sesión y carrito
- `src/components/` -> componentes reutilizables
- `src/layouts/` -> estructuras por tipo de usuario
- `src/pages/<rol>/` -> pantallas de cada actor

## Primera vez

```bash
npm create vite@latest . -- --template react   # elegir "Ignore files and continue"
npm install
cp .env.example .env
npm run dev
```

La URL del backend se configura en `.env` con `VITE_API_URL`.
