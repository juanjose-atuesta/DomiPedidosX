from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import (
    Categoria,
    GrupoOpcion,
    OpcionProducto,
    Producto,
    TipoGrupoOpcion,
)

PASSWORD = "ClaveSegura#2024"


class MenuGestionTests(APITestCase):
    def setUp(self):
        self.admin = self._crear_usuario(Rol.ADMIN, "admin.menu@example.com")
        self.operador = self._crear_usuario(
            Rol.OPERADOR, "operador.menu@example.com"
        )
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.menu@example.com"
        )
        self.repartidor = self._crear_usuario(
            Rol.REPARTIDOR, "repartidor.menu@example.com"
        )

        self.admin_token = self._token(self.admin)
        self.operador_token = self._token(self.operador)
        self.cliente_token = self._token(self.cliente)
        self.repartidor_token = self._token(self.repartidor)

        self.categoria = Categoria.objects.create(
            nombre="Platos principales", orden=1
        )
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre="Hamburguesa clasica",
            descripcion="Carne, queso y vegetales",
            precio_base=Decimal("25000.00"),
            tiempo_preparacion_min=20,
        )

        self.categoria_list_url = reverse("categoria_list_create")
        self.categoria_detail_url = reverse(
            "categoria_detail", args=[self.categoria.pk]
        )
        self.producto_list_url = reverse("producto_list_create")
        self.producto_detail_url = reverse(
            "producto_detail", args=[self.producto.pk]
        )
        self.producto_opciones_url = reverse(
            "producto_opciones", args=[self.producto.pk]
        )

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Menu",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload_producto(self, **overrides):
        data = {
            "categoria_id": str(self.categoria.pk),
            "nombre": "Pizza margarita",
            "descripcion": "Tomate y queso",
            "precio_base": "18900.50",
            "tiempo_preparacion_min": 15,
        }
        data.update(overrides)
        return data

    def _payload_grupo(self, nombre, tipo, opciones=None, **overrides):
        data = {
            "nombre": nombre,
            "tipo": tipo,
            "obligatorio": False,
            "max_selecciones": 1,
            "opciones": opciones or [],
        }
        data.update(overrides)
        return data

    def _crear_grupo(self, nombre="Tamaño", tipo=TipoGrupoOpcion.TAMANO):
        grupo = GrupoOpcion.objects.create(
            producto=self.producto,
            nombre=nombre,
            tipo=tipo,
            obligatorio=True,
            max_selecciones=1,
        )
        OpcionProducto.objects.create(
            grupo=grupo, nombre="Personal", precio_adicional=Decimal("0.00")
        )
        return grupo

    def test_admin_y_operador_pueden_crear_categoria(self):
        for token, nombre in (
            (self.admin_token, "Bebidas"),
            (self.operador_token, "Postres"),
        ):
            with self.subTest(nombre=nombre):
                response = self.client.post(
                    self.categoria_list_url,
                    {
                        "nombre": nombre,
                        "descripcion": "Categoria de prueba",
                        "orden": 2,
                    },
                    format="json",
                    **self._auth(token),
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["nombre"], nombre)
                self.assertTrue(
                    Categoria.objects.filter(nombre=nombre).exists()
                )

    def test_operador_crea_producto_valido(self):
        response = self.client.post(
            self.producto_list_url,
            self._payload_producto(),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 2)

        producto = Producto.objects.get(nombre="Pizza margarita")
        self.assertEqual(producto.categoria, self.categoria)
        self.assertEqual(producto.precio_base, Decimal("18900.50"))
        self.assertEqual(producto.tiempo_preparacion_min, 15)
        self.assertEqual(
            response.json()["categoria_id"], str(self.categoria.pk)
        )

    def test_rechaza_precio_negativo_o_tiempo_invalido(self):
        casos = (
            {"precio_base": "-1.00"},
            {"tiempo_preparacion_min": 0},
            {"tiempo_preparacion_min": -1},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                response = self.client.post(
                    self.producto_list_url,
                    self._payload_producto(**cambios),
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertEqual(Producto.objects.count(), 1)

    def test_operador_actualiza_producto(self):
        response = self.client.patch(
            self.producto_detail_url,
            {
                "nombre": "Hamburguesa doble",
                "precio_base": "32000.00",
                "tiempo_preparacion_min": 25,
            },
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Hamburguesa doble")
        self.assertEqual(self.producto.precio_base, Decimal("32000.00"))
        self.assertEqual(self.producto.tiempo_preparacion_min, 25)

    def test_delete_producto_hace_borrado_logico(self):
        pk = self.producto.pk

        response = self.client.delete(
            self.producto_detail_url, **self._auth(self.operador_token)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)
        self.assertTrue(Producto.objects.filter(pk=pk).exists())

        self.producto.refresh_from_db()
        self.assertFalse(self.producto.disponible)

    def test_operador_actualiza_y_desactiva_categoria(self):
        response_patch = self.client.patch(
            self.categoria_detail_url,
            {"nombre": "Platos fuertes", "orden": 3},
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, "Platos fuertes")

        response_delete = self.client.delete(
            self.categoria_detail_url, **self._auth(self.operador_token)
        )

        self.assertEqual(response_delete.status_code, status.HTTP_200_OK)
        self.categoria.refresh_from_db()
        self.assertFalse(self.categoria.activa)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_crea_grupos_anidados_tamano_adicion_y_excluible(self):
        casos = (
            (
                "Tamaño",
                TipoGrupoOpcion.TAMANO,
                True,
                1,
                [
                    {"nombre": "Personal", "precio_adicional": "0.00"},
                    {"nombre": "Mediana", "precio_adicional": "3000.00"},
                    {"nombre": "Grande", "precio_adicional": "5000.00"},
                ],
            ),
            (
                "Adiciones",
                TipoGrupoOpcion.ADICION,
                False,
                3,
                [
                    {"nombre": "Queso extra", "precio_adicional": "2000.00"},
                    {"nombre": "Tocineta", "precio_adicional": "2500.00"},
                ],
            ),
            (
                "Ingredientes excluibles",
                TipoGrupoOpcion.EXCLUIBLE,
                False,
                5,
                [
                    {"nombre": "Sin cebolla", "precio_adicional": "0.00"},
                    {"nombre": "Sin tomate", "precio_adicional": "0.00"},
                ],
            ),
        )

        for nombre, tipo, obligatorio, maximo, opciones in casos:
            with self.subTest(tipo=tipo):
                response = self.client.post(
                    self.producto_opciones_url,
                    self._payload_grupo(
                        nombre,
                        tipo,
                        opciones,
                        obligatorio=obligatorio,
                        max_selecciones=maximo,
                    ),
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_201_CREATED
                )
                self.assertEqual(response.data["tipo"], tipo)

                grupo = GrupoOpcion.objects.get(
                    producto=self.producto, nombre=nombre
                )
                self.assertEqual(grupo.obligatorio, obligatorio)
                self.assertEqual(grupo.max_selecciones, maximo)
                self.assertEqual(grupo.opciones.count(), len(opciones))
                self.assertEqual(
                    len(response.data["opciones"]), len(opciones)
                )

        self.assertEqual(
            GrupoOpcion.objects.filter(producto=self.producto).count(), 3
        )
        self.assertEqual(
            OpcionProducto.objects.filter(grupo__producto=self.producto).count(),
            7,
        )

    def test_actualizar_grupo_reemplaza_sus_opciones(self):
        self.client.post(
            self.producto_opciones_url,
            self._payload_grupo(
                "Adiciones",
                TipoGrupoOpcion.ADICION,
                [
                    {"nombre": "Queso", "precio_adicional": "2000.00"},
                    {"nombre": "Tocineta", "precio_adicional": "2500.00"},
                ],
                max_selecciones=2,
            ),
            format="json",
            **self._auth(self.operador_token),
        )

        response = self.client.post(
            self.producto_opciones_url,
            self._payload_grupo(
                "Adiciones",
                TipoGrupoOpcion.ADICION,
                [{"nombre": "Jalapeños", "precio_adicional": "1500.00"}],
                max_selecciones=1,
            ),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        grupos = GrupoOpcion.objects.filter(
            producto=self.producto, nombre="Adiciones"
        )
        self.assertEqual(grupos.count(), 1)

        grupo = grupos.get()
        self.assertEqual(grupo.max_selecciones, 1)
        self.assertEqual(grupo.opciones.count(), 1)
        self.assertEqual(grupo.opciones.get().nombre, "Jalapeños")

    def test_consulta_publica_de_opciones_y_producto(self):
        grupo = self._crear_grupo()

        response_opciones = self.client.get(self.producto_opciones_url)
        response_producto = self.client.get(self.producto_detail_url)

        self.assertEqual(response_opciones.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_opciones.data), 1)
        self.assertEqual(response_opciones.data[0]["id"], str(grupo.pk))
        self.assertEqual(len(response_opciones.data[0]["opciones"]), 1)

        self.assertEqual(response_producto.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response_producto.data["grupos_opcion"]), 1
        )

    def test_lista_categorias_solo_incluye_activas(self):
        inactiva = Categoria.objects.create(
            nombre="Categoria oculta", activa=False
        )

        response = self.client.get(self.categoria_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {categoria["id"] for categoria in response.data}
        self.assertIn(str(self.categoria.pk), ids)
        self.assertNotIn(str(inactiva.pk), ids)

    def test_detalle_categoria_inactiva_solo_visible_para_gestores(self):
        self.categoria.activa = False
        self.categoria.save(update_fields=["activa"])

        response_publica = self.client.get(self.categoria_detail_url)
        response_cliente = self.client.get(
            self.categoria_detail_url, **self._auth(self.cliente_token)
        )
        response_operador = self.client.get(
            self.categoria_detail_url, **self._auth(self.operador_token)
        )

        self.assertEqual(
            response_publica.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            response_cliente.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            response_operador.status_code, status.HTTP_200_OK
        )

    def test_lista_productos_solo_incluye_disponibles(self):
        no_disponible = Producto.objects.create(
            categoria=self.categoria,
            nombre="Producto agotado",
            precio_base=Decimal("10000.00"),
            tiempo_preparacion_min=10,
            disponible=False,
        )

        response = self.client.get(self.producto_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {producto["id"] for producto in response.data}
        self.assertIn(str(self.producto.pk), ids)
        self.assertNotIn(str(no_disponible.pk), ids)

    def test_detalle_producto_no_disponible_solo_visible_para_gestores(self):
        self.producto.disponible = False
        self.producto.save(update_fields=["disponible"])
        opciones_url = self.producto_opciones_url

        response_publica = self.client.get(self.producto_detail_url)
        response_cliente = self.client.get(
            self.producto_detail_url, **self._auth(self.cliente_token)
        )
        response_admin = self.client.get(
            self.producto_detail_url, **self._auth(self.admin_token)
        )
        response_opciones_cliente = self.client.get(
            opciones_url, **self._auth(self.cliente_token)
        )

        self.assertEqual(
            response_publica.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            response_cliente.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_opciones_cliente.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_clientes_y_repartidores_no_pueden_escribir_menu(self):
        payload_categoria = {"nombre": "No permitida"}
        payload_producto = self._payload_producto(nombre="No permitido")
        payload_grupo = self._payload_grupo(
            "No permitido", TipoGrupoOpcion.ADICION
        )

        for nombre_rol, token in (
            ("cliente", self.cliente_token),
            ("repartidor", self.repartidor_token),
        ):
            for metodo, url, payload in (
                ("post", self.categoria_list_url, payload_categoria),
                ("post", self.producto_list_url, payload_producto),
                ("post", self.producto_opciones_url, payload_grupo),
                ("patch", self.producto_detail_url, {"nombre": "No permitido"}),
                ("delete", self.producto_detail_url, {}),
            ):
                with self.subTest(rol=nombre_rol, metodo=metodo):
                    response = getattr(self.client, metodo)(
                        url,
                        payload,
                        format="json",
                        **self._auth(token),
                    )
                    self.assertEqual(
                        response.status_code, status.HTTP_403_FORBIDDEN
                    )

        self.assertEqual(Categoria.objects.count(), 1)
        self.assertEqual(Producto.objects.count(), 1)

    def test_sin_token_da_401_en_escritura(self):
        payload = self._payload_producto()

        for metodo, url in (
            ("post", self.categoria_list_url),
            ("post", self.producto_list_url),
            ("post", self.producto_opciones_url),
            ("patch", self.producto_detail_url),
            ("delete", self.producto_detail_url),
        ):
            with self.subTest(metodo=metodo):
                response = getattr(self.client, metodo)(
                    url, payload, format="json"
                )
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED
                )

        self.assertEqual(Categoria.objects.count(), 1)
        self.assertEqual(Producto.objects.count(), 1)
