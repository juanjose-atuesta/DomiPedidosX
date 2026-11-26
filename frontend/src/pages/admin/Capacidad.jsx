import { useState } from "react"
import { useParams } from "react-router-dom"
import AdminLayout from "../../layouts/AdminLayout"
import Boton from "../../components/Boton"

export default function Capacidad() {
  const { id } = useParams()
  return (
    <AdminLayout titulo="Capacidad de la Sede">
      <p>Configuración de topes para la sede {id}</p>
    </AdminLayout>
  )
}