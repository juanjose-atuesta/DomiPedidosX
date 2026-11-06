from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_de_rol, negocio_prueba
from apps.menu.models import Producto
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import Promocion, PromocionProducto

PASSWORD = "ClaveSegura#2024"


class PromocionTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.admin = self._crear_usuario(Rol.ADMIN, "admin.promo@example.com")
        self.operador = self._crear_usuario(
            Rol.OPERADOR, "operador.promo@example.com"
        )
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.promo@example.com"
        )
        self.repartidor = self._crear_usuario(
            Rol.REPARTIDOR, "repartidor.promo@example.com"
        )

        self.admin_token = self._token(self.admin)
        self.operador_token = self._token(self.operador)
        self.cliente_token = self._token(self.cliente)
        self.repartidor_token = self._token(self.repartidor)

        self.sede = Sede.objects.create(
            negocio=negocio_prueba(),
            nombre="Sede principal",
            direccion="Calle 1 # 2-3",
        )
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)
        self.otra_sede = Sede.objects.create(
            negocio=negocio_prueba(),
            nombre="Sede ajena",
            direccion="Calle 9 # 8-7",
        )
        self.producto_1 = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Hamburguesa",
            precio_base=Decimal("12000.00"),
            tiempo_preparacion_min=10,
        )
        self.producto_2 = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Papas",
            precio_base=Decimal("5000.00"),
            tiempo_preparacion_min=8,
        )

        self.promocion_list_url = reverse("promocion_list_create")

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol),
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Promocion",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload_promocion(self, tipo="porcentaje", **overrides):
        data = {
            "sede_id": str(self.sede.pk),
            "nombre": "Promocion de prueba",
            "descripcion": "Descuento de prueba",
            "codigo": "PROMO10",
            "pedido_minimo": "10000.00",
            "cupo_maximo_diario": 50,
            "fecha_inicio": str(self.hoy),
            "fecha_fin": str(self.hoy + timedelta(days=5)),
            "productos_ids": [str(self.producto_1.pk)],
        }
        if tipo == "porcentaje":
            data["porcentaje_descuento"] = "10.00"
        else:
            data["monto_descuento"] = "5000.00"
        data.update(overrides)
        return data

    def _crear_promocion(self, **overrides):
        response = self.client.post(
            self.promocion_list_url,
            self._payload_promocion(**overrides),
            format="json",
            **self._auth(self.operador_token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def _promocion_orm(self, **overrides):
        data = {
            "nombre": "Promocion ORM",
            "porcentaje_descuento": Decimal("10.00"),
            "cupo_maximo_diario": 20,
            "fecha_inicio": self.hoy - timedelta(days=1),
            "fecha_fin": self.hoy + timedelta(days=1),
        }
        data.update(overrides)
        return Promocion.objects.create(negocio=negocio_prueba(), **data)

    def test_admin_y_operador_crean_promocion_porcentaje_y_monto(self):
        casos = (
            (self.admin_token, "porcentaje", "Promo admin"),
            (self.operador_token, "monto", "Promo operador"),
        )

        for token, tipo, nombre in casos:
            with self.subTest(tipo=tipo):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(
                        tipo=tipo, nombre=nombre, codigo=None
                    ),
                    format="json",
                    **self._auth(token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_201_CREATED
                )
                self.assertEqual(response.data["nombre"], nombre)
                self.assertEqual(
                    str(response.data["sede_id"]), str(self.sede.pk)
                )

                promocion = Promocion.objects.get(nombre=nombre)
                self.assertEqual(promocion.cupo_maximo_diario, 50)
                self.assertEqual(promocion.productos_aplicables.count(), 1)

                if tipo == "porcentaje":
                    self.assertEqual(
                        promocion.porcentaje_descuento, Decimal("10.00")
                    )
                    self.assertIsNone(promocion.monto_descuento)
                else:
                    self.assertEqual(
                        promocion.monto_descuento, Decimal("5000.00")
                    )
                    self.assertIsNone(promocion.porcentaje_descuento)

    def test_cupo_maximo_diario_es_obligatorio(self):
        payload = self._payload_promocion()
        payload.pop("cupo_maximo_diario")

        response = self.client.post(
            self.promocion_list_url,
            payload,
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cupo_maximo_diario", response.data)
        self.assertFalse(Promocion.objects.exists())

        for cupo in (0, -1, None):
            with self.subTest(cupo=cupo):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(
                        cupo_maximo_diario=cupo
                    ),
                    format="json",
                    **self._auth(self.operador_token),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_rechaza_descuento_ambos_o_ninguno(self):
        payload_ambos = self._payload_promocion()
        payload_ambos["monto_descuento"] = "5000.00"

        payload_ninguno = self._payload_promocion()
        payload_ninguno.pop("porcentaje_descuento")

        for payload in (payload_ambos, payload_ninguno):
            with self.subTest(payload=payload):
                response = self.client.post(
                    self.promocion_list_url,
                    payload,
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertFalse(Promocion.objects.exists())

    def test_rechaza_fechas_invalidas(self):
        casos = (
            {
                "fecha_inicio": str(self.hoy),
                "fecha_fin": str(self.hoy - timedelta(days=1)),
            },
            {"fecha_inicio": "fecha-invalida"},
            {"fecha_fin": "fecha-invalida"},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(**cambios),
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertFalse(Promocion.objects.exists())

    def test_rechaza_porcentaje_fuera_de_rango(self):
        for porcentaje in ("0.00", "100.01", "-1.00"):
            with self.subTest(porcentaje=porcentaje):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(
                        porcentaje_descuento=porcentaje
                    ),
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_crea_promocion_global_sin_codigo_y_sin_productos(self):
        payload = self._payload_promocion(
            sede_id=None,
            codigo="  ",
            productos_ids=[],
        )

        response = self.client.post(
            self.promocion_list_url,
            payload,
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["sede_id"])
        self.assertIsNone(response.data["codigo"])
        self.assertEqual(
            PromocionProducto.objects.count(),
            0,
        )

    def test_rechaza_codigo_duplicado(self):
        self._crear_promocion()
        response = self.client.post(
            self.promocion_list_url,
            self._payload_promocion(nombre="Otra promocion"),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            "detail" in response.data or "codigo" in response.data
        )

    def test_rechaza_sede_o_producto_inexistente(self):
        from uuid import uuid4

        casos = (
            {"sede_id": str(uuid4())},
            {"productos_ids": [str(uuid4())]},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(**cambios),
                    format="json",
                    **self._auth(self.operador_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertFalse(Promocion.objects.exists())

    def test_lista_publica_solo_promociones_activas_y_vigentes(self):
        vigente = self._promocion_orm(nombre="Vigente")
        inactiva = self._promocion_orm(nombre="Inactiva", activa=False)
        vencida = self._promocion_orm(
            nombre="Vencida",
            fecha_inicio=self.hoy - timedelta(days=10),
            fecha_fin=self.hoy - timedelta(days=1),
        )

        response = self.client.get(self.promocion_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {promocion["id"] for promocion in response.data}
        self.assertIn(str(vigente.pk), ids)
        self.assertNotIn(str(inactiva.pk), ids)
        self.assertNotIn(str(vencida.pk), ids)

    def test_detalle_publico_oculta_inactiva_o_vencida(self):
        inactiva = self._promocion_orm(nombre="Inactiva", activa=False)
        vencida = self._promocion_orm(
            nombre="Vencida",
            fecha_inicio=self.hoy - timedelta(days=10),
            fecha_fin=self.hoy - timedelta(days=1),
        )

        for promocion in (inactiva, vencida):
            with self.subTest(promocion=promocion.nombre):
                url = reverse("promocion_detail", args=[promocion.pk])
                response_publica = self.client.get(url)
                response_operador = self.client.get(
                    url, **self._auth(self.operador_token)
                )

                self.assertEqual(
                    response_publica.status_code,
                    status.HTTP_404_NOT_FOUND,
                )
                self.assertEqual(
                    response_operador.status_code, status.HTTP_200_OK
                )

    def test_operador_actualiza_promocion_y_reemplaza_productos(self):
        response = self._crear_promocion()
        promocion = Promocion.objects.get(nombre="Promocion de prueba")
        detail_url = reverse("promocion_detail", args=[promocion.pk])

        response = self.client.patch(
            detail_url,
            {
                "nombre": "Promocion actualizada",
                "porcentaje_descuento": None,
                "monto_descuento": "3000.00",
                "cupo_maximo_diario": 80,
                "productos_ids": [str(self.producto_2.pk)],
            },
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        promocion.refresh_from_db()
        self.assertEqual(promocion.nombre, "Promocion actualizada")
        self.assertIsNone(promocion.porcentaje_descuento)
        self.assertEqual(promocion.monto_descuento, Decimal("3000.00"))
        self.assertEqual(promocion.cupo_maximo_diario, 80)
        self.assertEqual(promocion.productos_aplicables.count(), 1)
        self.assertEqual(
            promocion.productos_aplicables.get().producto,
            self.producto_2,
        )
        self.assertIsNotNone(response.data["id"])

    def test_delete_promocion_hace_borrado_logico(self):
        self._crear_promocion()
        promocion = Promocion.objects.get(nombre="Promocion de prueba")
        detail_url = reverse("promocion_detail", args=[promocion.pk])

        response = self.client.delete(
            detail_url, **self._auth(self.operador_token)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)
        promocion.refresh_from_db()
        self.assertFalse(promocion.activa)
        self.assertTrue(Promocion.objects.filter(pk=promocion.pk).exists())

    def test_operador_no_crea_promocion_global_ni_de_sede_ajena(self):
        for sede_id in (None, str(self.otra_sede.pk)):
            with self.subTest(sede_id=sede_id):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(sede_id=sede_id),
                    format="json",
                    **self._auth(self.operador_token),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN
                )

        self.assertFalse(Promocion.objects.exists())

    def test_operador_no_edita_ni_desactiva_promocion_global_o_ajena(self):
        promociones = (
            self._promocion_orm(nombre="Global"),
            self._promocion_orm(nombre="Ajena", sede=self.otra_sede),
        )

        for promocion in promociones:
            with self.subTest(promocion=promocion.nombre):
                url = reverse("promocion_detail", args=[promocion.pk])

                response_patch = self.client.patch(
                    url,
                    {"nombre": "Cambiada"},
                    format="json",
                    **self._auth(self.operador_token),
                )
                response_delete = self.client.delete(
                    url, **self._auth(self.operador_token)
                )

                self.assertEqual(
                    response_patch.status_code, status.HTTP_403_FORBIDDEN
                )
                self.assertEqual(
                    response_delete.status_code, status.HTTP_403_FORBIDDEN
                )
                nombre_original = promocion.nombre
                promocion.refresh_from_db()
                self.assertEqual(promocion.nombre, nombre_original)
                self.assertTrue(promocion.activa)

    def test_operador_no_mueve_su_promocion_a_otra_sede_ni_la_vuelve_global(self):
        promocion = self._promocion_orm(sede=self.sede)
        url = reverse("promocion_detail", args=[promocion.pk])

        for sede_id in (None, str(self.otra_sede.pk)):
            with self.subTest(sede_id=sede_id):
                response = self.client.patch(
                    url,
                    {"sede_id": sede_id},
                    format="json",
                    **self._auth(self.operador_token),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN
                )
                promocion.refresh_from_db()
                self.assertEqual(promocion.sede, self.sede)

    def test_admin_gestiona_promocion_global(self):
        promocion = self._promocion_orm(nombre="Global")
        url = reverse("promocion_detail", args=[promocion.pk])

        response = self.client.patch(
            url,
            {"nombre": "Global editada"},
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Global editada")

    def test_clientes_repartidores_y_anonimos_no_escriben_promociones(self):
        for token in (self.cliente_token, self.repartidor_token):
            with self.subTest(token=token):
                response = self.client.post(
                    self.promocion_list_url,
                    self._payload_promocion(),
                    format="json",
                    **self._auth(token),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN
                )

        response_anonima = self.client.post(
            self.promocion_list_url,
            self._payload_promocion(),
            format="json",
        )
        self.assertEqual(
            response_anonima.status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertFalse(Promocion.objects.exists())

    def test_gestion_incluye_inactivas_con_alcance_por_sede(self):
        propia = self._promocion_orm(
            nombre="Propia", sede=self.sede, activa=False
        )
        global_ = self._promocion_orm(nombre="Global")
        ajena = self._promocion_orm(nombre="Ajena", sede=self.otra_sede)
        parametros = {"incluir_inactivas": "true"}

        def ids(response):
            return {promocion["id"] for promocion in response.data}

        response = self.client.get(
            self.promocion_list_url, parametros, **self._auth(self.operador_token)
        )
        self.assertEqual(ids(response), {str(propia.pk), str(global_.pk)})

        response = self.client.get(
            self.promocion_list_url, parametros, **self._auth(self.admin_token)
        )
        self.assertEqual(
            ids(response), {str(propia.pk), str(global_.pk), str(ajena.pk)}
        )

        response = self.client.get(self.promocion_list_url, parametros)
        self.assertEqual(ids(response), {str(global_.pk), str(ajena.pk)})

    def test_crea_promocion_con_el_payload_del_formulario(self):
        response = self.client.post(
            self.promocion_list_url,
            {
                "sede_id": str(self.sede.pk),
                "nombre": "Desde formulario",
                "descripcion": "",
                "porcentaje_descuento": None,
                "monto_descuento": "5000",
                "pedido_minimo": "0",
                "cupo_maximo_diario": "10",
                "fecha_inicio": str(self.hoy),
                "fecha_fin": str(self.hoy),
                "productos_ids": [str(self.producto_1.pk)],
            },
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
