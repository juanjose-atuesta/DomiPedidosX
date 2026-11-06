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
import Pedidos from "./pages/operador/Pedidos"
import NuevoPedido from "./pages/operador/NuevoPedido"
import Carrito from "./pages/cliente/Carrito"
import PedidoRecibido from "./pages/cliente/PedidoRecibido"
import PedidosCliente from "./pages/cliente/Pedidos"
import TableroCocina from "./pages/cocina/TableroCocina"
import PedidosRepartidor from "./pages/repartidor/PedidosRepartidor"
import AccesoDenegado from "./pages/AccesoDenegado"
import PanelNoDisponible from "./pages/PanelNoDisponible"
import Direcciones from "./pages/cliente/Direcciones"
import Perfil from "./pages/cliente/Perfil"
import AgregarDireccion from "./pages/cliente/AgregarDireccion"
import Bienvenida from "./pages/auth/Bienvenida"
import Login from "./pages/auth/Login"
import RecuperarContrasena from "./pages/auth/RecuperarContrasena"
import Registro from "./pages/auth/Registro"
import Inicio from "./pages/cliente/Inicio"
import Producto from "./pages/cliente/Producto"
import RegistroRestaurante from "./pages/auth/RegistroRestaurante"
import RegistroAdministrador from "./pages/auth/RegistroAdministrador"
import RutaProtegida from "./routes/RutaProtegida"
import { ROLES_POR_SECCION } from "./utils/roles"

const ADMIN = ROLES_POR_SECCION["/admin"]
const OPERADOR = ROLES_POR_SECCION["/operador"]
const CLIENTE = ROLES_POR_SECCION["/cliente"]
const COCINA = ROLES_POR_SECCION["/cocina"]
const REPARTIDOR = ROLES_POR_SECCION["/repartidor"]

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Autenticación */}
      <Route path="/login" element={<Login />} />
      <Route path="/iniciar-sesion" element={<Navigate to="/login" replace />} />
      <Route path="/bienvenida" element={<Bienvenida />} />
      <Route path="/recuperar-contrasena" element={<RecuperarContrasena />} />
      <Route path="/registro" element={<Registro />} />
      <Route path="/registro-restaurante" element={<RegistroRestaurante />} />
      <Route path="/registro-administrador" element={<RegistroAdministrador />} />

      {/* Administración */}
      <Route
        path="/admin/usuarios"
        element={
          <RutaProtegida roles={ADMIN}>
            <Usuarios />
          </RutaProtegida>
        }
      />
      <Route
        path="/admin/usuarios/nueva"
        element={
          <RutaProtegida roles={ADMIN}>
            <CrearCuentaPersonal />
          </RutaProtegida>
        }
      />
      <Route
        path="/admin/sedes"
        element={
          <RutaProtegida roles={ADMIN}>
            <Sedes />
          </RutaProtegida>
        }
      />
      <Route
        path="/admin/sedes/nueva"
        element={
          <RutaProtegida roles={ADMIN}>
            <FormularioSede />
          </RutaProtegida>
        }
      />
      <Route
        path="/admin/sedes/:id/editar"
        element={
          <RutaProtegida roles={ADMIN}>
            <FormularioSede />
          </RutaProtegida>
        }
      />

      {/* Operación de sede */}
      <Route
        path="/operador/pedidos"
        element={
          <RutaProtegida roles={OPERADOR}>
            <Pedidos />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/pedidos/nuevo"
        element={
          <RutaProtegida roles={OPERADOR}>
            <NuevoPedido />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/categorias"
        element={
          <RutaProtegida roles={OPERADOR}>
            <Categorias />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/productos"
        element={
          <RutaProtegida roles={OPERADOR}>
            <Productos />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/productos/nuevo"
        element={
          <RutaProtegida roles={OPERADOR}>
            <FormularioProducto />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/productos/:id/editar"
        element={
          <RutaProtegida roles={OPERADOR}>
            <FormularioProducto />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/promociones"
        element={
          <RutaProtegida roles={OPERADOR}>
            <Promociones />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/promociones/nueva"
        element={
          <RutaProtegida roles={OPERADOR}>
            <FormularioPromocion />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/promociones/:id/editar"
        element={
          <RutaProtegida roles={OPERADOR}>
            <FormularioPromocion />
          </RutaProtegida>
        }
      />
      <Route
        path="/operador/inventario"
        element={
          <RutaProtegida roles={OPERADOR}>
            <Inventario />
          </RutaProtegida>
        }
      />

      {/* Cliente */}
      <Route
        path="/cliente"
        element={
          <RutaProtegida roles={CLIENTE}>
            <Inicio />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/producto/:id"
        element={
          <RutaProtegida roles={CLIENTE}>
            <Producto />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/carrito"
        element={
          <RutaProtegida roles={CLIENTE}>
            <Carrito />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/pedido-recibido"
        element={
          <RutaProtegida roles={CLIENTE}>
            <PedidoRecibido />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/pedidos"
        element={
          <RutaProtegida roles={CLIENTE}>
            <PedidosCliente />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/direcciones"
        element={
          <RutaProtegida roles={CLIENTE}>
            <Direcciones />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/direcciones/nueva"
        element={
          <RutaProtegida roles={CLIENTE}>
            <AgregarDireccion />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/direcciones/:id/editar"
        element={
          <RutaProtegida roles={CLIENTE}>
            <AgregarDireccion />
          </RutaProtegida>
        }
      />
      <Route
        path="/cliente/perfil"
        element={
          <RutaProtegida roles={CLIENTE}>
            <Perfil />
          </RutaProtegida>
        }
      />

      {/* Cocina */}
      <Route
        path="/cocina"
        element={
          <RutaProtegida roles={COCINA}>
            <TableroCocina />
          </RutaProtegida>
        }
      />

      {/* Repartidor */}
      <Route
        path="/repartidor"
        element={
          <RutaProtegida roles={REPARTIDOR}>
            <PedidosRepartidor />
          </RutaProtegida>
        }
      />

      <Route
        path="/panel-no-disponible"
        element={
          <RutaProtegida>
            <PanelNoDisponible />
          </RutaProtegida>
        }
      />
      <Route path="/acceso-denegado" element={<AccesoDenegado />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
