export const CATEGORIAS = ["Hamburguesas", "Acompañamientos", "Bebidas", "Postres"]

export const PRODUCTOS = [
  {
    id: 1, nombre: "Hamburguesa clásica", categoria: "Hamburguesas", precio: 18000, tiempo: 15,
    descripcion: "Carne de res, queso, lechuga y tomate", disponible: true, activo: true,
    tamanos: [{ nombre: "Sencilla", extra: 0 }, { nombre: "Doble", extra: 4000 }],
    adiciones: [{ nombre: "Queso extra", extra: 2000 }, { nombre: "Tocineta", extra: 3000 }],
    excluibles: [{ nombre: "Cebolla", extra: 0 }, { nombre: "Tomate", extra: 0 }],
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