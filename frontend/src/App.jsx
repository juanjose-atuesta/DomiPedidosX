import { Navigate, Route, Routes } from "react-router-dom"
import Usuarios from "./pages/admin/Usuarios"
import CrearCuentaPersonal from "./pages/admin/CrearCuentaPersonal"
import Sedes from "./pages/admin/Sedes"
import FormularioSede from "./pages/admin/FormularioSede"
import Categorias from "./pages/operador/Categorias"
import Productos from "./pages/operador/Productos"
import FormularioProducto from "./pages/operador/FormularioProducto"
import Promociones from "./pages/operador/Promociones"
import FormularioPromocion from "./pages/operador/FormularioPromocion"
import Inventario from "./pages/operador/Inventario"
import AccesoDenegado from "./pages/AccesoDenegado"
import Direcciones from "./pages/cliente/Direcciones"
import Perfil from "./pages/cliente/Perfil"
import AgregarDireccion from "./pages/cliente/AgregarDireccion"

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
      <Route path="/operador/productos/nuevo" element={<FormularioProducto />} />
      <Route path="/operador/productos/:id/editar" element={<FormularioProducto />} />
      <Route path="/operador/promociones" element={<Promociones />} />
      <Route path="/operador/promociones/nueva" element={<FormularioPromocion />} />
      <Route path="/operador/promociones/:id/editar" element={<FormularioPromocion />} />
      <Route path="/operador/inventario" element={<Inventario />} />
      <Route path="/acceso-denegado" element={<AccesoDenegado />} />
      <Route path="/cliente/direcciones" element={<Direcciones />} />
      <Route path="/cliente/perfil" element={<Perfil />} />
      <Route path="/cliente/direcciones/nueva" element={<AgregarDireccion />} />
      <Route path="/cliente/direcciones/:id/editar" element={<AgregarDireccion />} />
      <Route path="*" element={<p className="p-8 text-texto">Página en construcción</p>} />
    </Routes>
  )
}