from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.menu.models import Producto
from apps.notificaciones.models import (
    CanalNotificacion,
    Notificacion,
    TipoNotificacion,
)
from apps.sedes.models import Sede
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import InventarioSede

PASSWORD = "ClaveSegura#2024"


class InventarioSedeTests(APITestCase):
    def setUp(self):
        self.admin = self._crear_usuario(Rol.ADMIN, "admin.inventario@example.com")
        self.operador = self._crear_usuario(
            Rol.OPERADOR, "operador.inventario@example.com"
        )
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.inventario@example.com"
        )

        self.admin_token = self._token(self.admin)
        self.operador_token = self._token(self.operador)
        self.cliente_token = self._token(self.cliente)

        self.sede = Sede.objects.create(
            nombre="Sede Centro",
            direccion="Calle 10 # 20-30",
        )
        self.producto = Producto.objects.create(
            nombre="Hamburguesa",
            precio_base=Decimal("15000.00"),
            tiempo_preparacion_min=15,
        )
        self.producto_2 = Producto.objects.create(
            nombre="Limonada",
            precio_base=Decimal("5000.00"),
            tiempo_preparacion_min=5,
        )

        self.inventario_url = reverse(
            "inventario_sede", args=[self.sede.pk]
        )

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Inventario",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload_inventario(self, producto=None, **overrides):
        data = {
            "producto_id": str((producto or self.producto).pk),
            "disponible_en_sede": True,
            "controla_stock": True,
            "stock_actual": 10,
            "stock_minimo": 5,
        }
        data.update(overrides)
        return data

    def test_operador_asigna_y_actualiza_inventario(self):
        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            str(response.data["producto_id"]), str(self.producto.pk)
        )
        self.assertFalse(response.data["agotado"])
        self.assertFalse(response.data["stock_bajo"])
        self.assertEqual(InventarioSede.objects.count(), 1)

        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(stock_actual=4),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock_actual"], 4)
        self.assertTrue(response.data["stock_bajo"])
        self.assertFalse(response.data["agotado"])
        self.assertEqual(InventarioSede.objects.count(), 1)

        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(stock_actual=0),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["agotado"])
        self.assertTrue(response.data["stock_bajo"])

    def test_admin_tambien_puede_gestionar_inventario(self):
        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(stock_actual=8),
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            InventarioSede.objects.filter(
                sede=self.sede, producto=self.producto
            ).exists()
        )

    def test_genera_alerta_stock_bajo_al_guardar_stock_igual_o_menor(self):
        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(stock_actual=5, stock_minimo=5),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        alertas = Notificacion.objects.filter(
            tipo=TipoNotificacion.ALERTA_STOCK_BAJO
        )
        self.assertEqual(alertas.count(), 1)

        alerta = alertas.get()
        self.assertEqual(alerta.sede, self.sede)
        self.assertEqual(alerta.canal, CanalNotificacion.SISTEMA)
        self.assertIn(self.producto.nombre, alerta.mensaje)
        self.assertIn("5", alerta.mensaje)

    def test_no_genera_alerta_si_stock_es_superior_o_no_controla_stock(self):
        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(stock_actual=10, stock_minimo=5),
            format="json",
            **self._auth(self.operador_token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(
                producto=self.producto_2,
                controla_stock=False,
                stock_actual=0,
                stock_minimo=5,
            ),
            format="json",
            **self._auth(self.operador_token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertFalse(
            Notificacion.objects.filter(
                tipo=TipoNotificacion.ALERTA_STOCK_BAJO
            ).exists()
        )

    def test_cliente_no_puede_modificar_inventario(self):
        response = self.client.post(
            self.inventario_url,
            self._payload_inventario(),
            format="json",
            **self._auth(self.cliente_token),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(InventarioSede.objects.exists())

        response_anonima = self.client.post(
            self.inventario_url,
            self._payload_inventario(),
            format="json",
        )
        self.assertEqual(
            response_anonima.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_rechaza_sede_inactiva_producto_no_disponible_y_stock_invalido(self):
        sede_inactiva = Sede.objects.create(
            nombre="Sede cerrada",
            direccion="Calle 1 # 2-3",
            activa=False,
        )
        producto_no_disponible = Producto.objects.create(
            nombre="Producto oculto",
            precio_base=Decimal("10000.00"),
            tiempo_preparacion_min=10,
            disponible=False,
        )

        casos = (
            (
                reverse("inventario_sede", args=[sede_inactiva.pk]),
                self._payload_inventario(),
            ),
            (
                self.inventario_url,
                self._payload_inventario(producto=producto_no_disponible),
            ),
            (
                self.inventario_url,
                self._payload_inventario(stock_actual=-1),
            ),
        )

        for url, payload in casos:
            with self.subTest(url=url, payload=payload):
                response = self.client.post(
                    url,
                    payload,
                    format="json",
                    **self._auth(self.operador_token),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

        self.assertFalse(InventarioSede.objects.exists())

    def test_lista_inventario_filtrado_por_sede(self):
        otra_sede = Sede.objects.create(
            nombre="Sede Norte",
            direccion="Calle 4 # 5-6",
        )
        InventarioSede.objects.create(
            sede=self.sede,
            producto=self.producto,
            stock_actual=4,
            stock_minimo=5,
        )
        InventarioSede.objects.create(
            sede=otra_sede,
            producto=self.producto_2,
            stock_actual=10,
            stock_minimo=5,
        )

        response = self.client.get(
            self.inventario_url, **self._auth(self.operador_token)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            str(response.data[0]["producto_id"]), str(self.producto.pk)
        )
        self.assertTrue(response.data[0]["stock_bajo"])

    def test_actualiza_disponibilidad_por_patch(self):
        InventarioSede.objects.create(
            sede=self.sede,
            producto=self.producto,
            disponible_en_sede=True,
            stock_actual=10,
            stock_minimo=5,
        )

        response = self.client.patch(
            self.inventario_url,
            {
                "producto_id": str(self.producto.pk),
                "disponible_en_sede": False,
            },
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["disponible_en_sede"])
        inventario = InventarioSede.objects.get(
            sede=self.sede, producto=self.producto
        )
        self.assertFalse(inventario.disponible_en_sede)

    def test_elimina_inventario_de_un_producto(self):
        InventarioSede.objects.create(
            sede=self.sede,
            producto=self.producto,
            stock_actual=10,
            stock_minimo=5,
        )

        response = self.client.delete(
            self.inventario_url,
            {"producto_id": str(self.producto.pk)},
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)
        self.assertFalse(
            InventarioSede.objects.filter(
                sede=self.sede, producto=self.producto
            ).exists()
        )
