from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventario.models import InventarioSede
from apps.menu.models import Producto, ProductoCombo
from apps.notificaciones.models import Notificacion, TipoNotificacion
from apps.sedes.models import Sede
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import DetallePedido, Pedido

PASSWORD = "ClaveSegura#2024"


class PedidoInventarioTests(APITestCase):
    def setUp(self):
        self.operador = self._crear_usuario(
            Rol.OPERADOR, "operador.pedidos@example.com"
        )
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.pedidos@example.com"
        )
        self.operador_token = self._token(self.operador)
        self.cliente_token = self._token(self.cliente)

        self.sede = Sede.objects.create(
            nombre="Sede Norte",
            direccion="Calle 20 # 30-40",
        )

        self.producto = Producto.objects.create(
            nombre="Hamburguesa",
            precio_base=Decimal("15000.00"),
            tiempo_preparacion_min=15,
        )
        self.adicional = Producto.objects.create(
            nombre="Limonada",
            precio_base=Decimal("5000.00"),
            tiempo_preparacion_min=5,
        )
        self.combo = Producto.objects.create(
            nombre="Combo Hamburguesa",
            precio_base=Decimal("20000.00"),
            tiempo_preparacion_min=20,
            es_combo=True,
        )
        ProductoCombo.objects.create(
            combo=self.combo,
            producto=self.producto,
            cantidad=2,
        )
        ProductoCombo.objects.create(
            combo=self.combo,
            producto=self.adicional,
            cantidad=1,
        )

        self.inventario_producto = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.producto,
            stock_actual=10,
            stock_minimo=3,
        )
        self.inventario_adicional = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.adicional,
            stock_actual=10,
            stock_minimo=3,
        )
        self.inventario_combo = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.combo,
            stock_actual=50,
            stock_minimo=3,
        )

        self.pedidos_url = reverse("pedido_list_create")

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Pedidos",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload(self, *, producto=None, cantidad=1, **overrides):
        data = {
            "sede_id": str(self.sede.pk),
            "cliente_nombre": "Ana Perez",
            "cliente_telefono": "3100000000",
            "metodo_pago": "efectivo",
            "detalles": [
                {
                    "producto_id": str((producto or self.producto).pk),
                    "cantidad": cantidad,
                }
            ],
        }
        data.update(overrides)
        return data

    def test_pedido_simple_descuenta_stock_de_la_sede(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(DetallePedido.objects.count(), 1)
        self.assertEqual(response.data["estado"], "recibido")
        self.assertEqual(len(response.data["detalles"]), 1)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 8)

    def test_pedido_con_combo_descuenta_todos_sus_componentes(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(producto=self.combo, cantidad=3),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.inventario_adicional.refresh_from_db()
        self.inventario_combo.refresh_from_db()

        self.assertEqual(self.inventario_producto.stock_actual, 4)
        self.assertEqual(self.inventario_adicional.stock_actual, 7)
        self.assertEqual(self.inventario_combo.stock_actual, 50)

    def test_stock_insuficiente_devuelve_400_y_revierte_todo(self):
        self.inventario_producto.stock_actual = 1
        self.inventario_producto.save(update_fields=["stock_actual"])

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Stock insuficiente para el producto", str(response.data))
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(DetallePedido.objects.count(), 0)
        self.assertEqual(Notificacion.objects.count(), 0)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 1)

    def test_descuento_hasta_el_minimo_genera_alerta_de_stock_bajo(self):
        self.inventario_producto.stock_actual = 10
        self.inventario_producto.stock_minimo = 5
        self.inventario_producto.save(
            update_fields=["stock_actual", "stock_minimo"]
        )

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=5),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 5)
        self.assertEqual(Notificacion.objects.count(), 1)
        self.assertEqual(
            Notificacion.objects.get().tipo,
            TipoNotificacion.ALERTA_STOCK_BAJO,
        )

    def test_producto_sin_control_de_stock_no_se_descuenta(self):
        self.inventario_producto.controla_stock = False
        self.inventario_producto.stock_actual = 1
        self.inventario_producto.save(
            update_fields=["controla_stock", "stock_actual"]
        )

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 1)

    def test_cliente_autenticado_puede_crear_pedido(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=1),
            format="json",
            **self._auth(self.cliente_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.creado_por, self.cliente)
