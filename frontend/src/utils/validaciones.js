export const MENSAJE_CONTRASENA = "Mínimo 8 caracteres, con una letra y un número"

export function contrasenaValida(contrasena) {
  return contrasena.length >= 8 && /[A-Za-z]/.test(contrasena) && /\d/.test(contrasena)
}