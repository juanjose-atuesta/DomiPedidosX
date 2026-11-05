import { Navigate, Route, Routes } from "react-router-dom"
import Usuarios from "./pages/admin/Usuarios"
import CrearCuentaPersonal from "./pages/admin/CrearCuentaPersonal"
import Sedes from "./pages/admin/Sedes"
import FormularioSede from "./pages/admin/FormularioSede"
import Categorias from "./pages/operador/Categorias"
import Productos from "./pages/operador/Productos"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/admin/usuarios" replace />} />
      <Route path="/admin/usuarios" element={<Usuarios />} />
      <Route path="/admin/usuarios/nueva" element={<CrearCuentaPersonal />} />
      <Route path="/admin/sedes" element={<Sedes />} />
      <Route path="/admin/sedes/nueva" element={<FormularioSede />} />
      <Route path="/admin/sedes/:id/editar" element={<FormularioSede />} />
      <Route path="/operador/categorias" element={<Categorias />} />
      <Route path="/operador/productos" element={<Productos />} />
      <Route path="*" element={<p className="p-8 text-texto">Página en construcción</p>} />
    </Routes>
  )
}