export const CATEGORIAS = ["Hamburguesas", "Acompañamientos", "Bebidas", "Postres"]

export const PRODUCTOS = [
  {
    id: 1, nombre: "Hamburguesa clásica", categoria: "Hamburguesas", precio: 18000, tiempo: 15,
    descripcion: "Carne de res, queso, lechuga y tomate", disponible: true, activo: true,
    detalle: "Hamburguesa con 120gr de carne agnus, tocineta, queso americano, pan artesanal, salsa de la casa, tomate, lechuga y cebolla morada.",
    tamanos: [{ nombre: "Pequeño", extra: 0 }, { nombre: "Mediano", extra: 3000 }, { nombre: "Grande", extra: 6000 }],
    adiciones: [{ nombre: "Tocineta", extra: 2500 }, { nombre: "Queso extra", extra: 2500 }, { nombre: "Papas", extra: 6000 }],
    excluibles: [{ nombre: "Cebolla", extra: 0 }, { nombre: "Tomate", extra: 0 }, { nombre: "Lechuga", extra: 0 }, { nombre: "Salsa", extra: 0 }],
  },
  {
    id: 2, nombre: "Papas fritas", categoria: "Acompañamientos", precio: 7000, tiempo: 8,
    descripcion: "Porción de papas crocantes", disponible: true, activo: true,
    tamanos: [{ nombre: "Mediana", extra: 0 }, { nombre: "Grande", extra: 3000 }],
    adiciones: [{ nombre: "Salsa de ajo", extra: 1000 }],
    excluibles: [],
  },
  {
    id: 3, nombre: "Limonada de coco", categoria: "Bebidas", precio: 9000, tiempo: 5,
    descripcion: "Limonada cremosa con coco", disponible: false, activo: true,
    tamanos: [{ nombre: "Vaso", extra: 0 }, { nombre: "Jarra", extra: 12000 }],
    adiciones: [],
    excluibles: [],
  },
  {
    id: 4, nombre: "Brownie", categoria: "Postres", precio: 8000, tiempo: 5,
    descripcion: "Brownie de chocolate con nueces", disponible: true, activo: true,
    tamanos: [],
    adiciones: [{ nombre: "Helado", extra: 3000 }],
    excluibles: [{ nombre: "Nueces", extra: 0 }],
  },
]