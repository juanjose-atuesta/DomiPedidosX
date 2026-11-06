const archivos = import.meta.glob("./*.{png,svg,jpg,jpeg,webp}", {
  eager: true,
  import: "default",
})

function buscar(nombre) {
  const clave = Object.keys(archivos).find(
    (k) => k.replace(/^\.\//, "").replace(/\.[^.]+$/, "") === nombre,
  )
  return clave ? archivos[clave] : undefined
}

export const fondoRojo = buscar("fondo-rojo")
export const fondoCrema = buscar("fondo-crema")
export const logoBlanco = buscar("logo-blanco")
export const iconoBolsaNaranja = buscar("icono-bolsa-naranja")
export const iconoBolsaRoja = buscar("icono-bolsa-roja")
export const fondoPerfil = buscar("fondo-perfil")
export const fotoHamburguesa = buscar("foto-hamburguesa")
export const fondoVino = buscar("fondo-vino")