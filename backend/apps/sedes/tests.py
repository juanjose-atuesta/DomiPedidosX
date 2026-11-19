from datetime import time, timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_de_rol, negocio_prueba
from apps.negocios.models import Negocio
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import Sede
from .services import crear_sede

PASSWORD = "ClaveSegura#2024"


class SedeGestionTests(APITestCase):
    def setUp(self):
        self.admin = self._crear_usuario(Rol.ADMIN, "admin.sedes@example.com")
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.sedes@example.com"
        )
        self.repartidor = self._crear_usuario(
            Rol.REPARTIDOR, "repartidor.sedes@example.com"
        )

        self.admin_token = self._token(self.admin)
        self.cliente_token = self._token(self.cliente)
        self.repartidor_token = self._token(self.repartidor)

        self.list_url = reverse("sede_list_create")

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol),
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Sedes",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload(self, **overrides):
        data = {
            "nombre": "Sede Centro",
            "direccion": "Calle 10 # 20-30",
            "telefono": "3001234567",
            "latitud": "4.60971000",
            "longitud": "-74.08175000",
            "horarios": [
                {
                    "dia_semana": 1,
                    "hora_apertura": "08:00:00",
                    "hora_cierre": "12:00:00",
                },
                {
                    "dia_semana": 1,
                    "hora_apertura": "14:00:00",
                    "hora_cierre": "18:00:00",
                },
            ],
        }
        data.update(overrides)
        return data

    def _crear_sede(self, nombre="Sede Norte", activa=True):
        sede = crear_sede(
            negocio=negocio_prueba(),
            nombre=nombre,
            direccion="Calle 1 # 2-3",
            telefono="3000000000",
            horarios=[
                {
                    "dia_semana": 1,
                    "hora_apertura": time(8, 0),
                    "hora_cierre": time(12, 0),
                },
                {
                    "dia_semana": 1,
                    "hora_apertura": time(14, 0),
                    "hora_cierre": time(18, 0),
                },
            ],
        )
        if not activa:
            sede.activa = False
            sede.save(update_fields=["activa"])
        return sede

    def _detail_url(self, sede):
        return reverse("sede_detail", args=[sede.pk])

    def test_admin_crea_sede_con_horarios_validos(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sede.objects.count(), 1)

        sede = Sede.objects.get()
        self.assertEqual(sede.nombre, "Sede Centro")
        self.assertEqual(sede.horarios.count(), 2)
        self.assertTrue(response.data["activa"])
        self.assertEqual(len(response.data["horarios"]), 2)

    def test_rechaza_hora_cierre_menor_o_igual_a_apertura(self):
        for apertura, cierre in (
            ("12:00:00", "11:00:00"),
            ("12:00:00", "12:00:00"),
        ):
            with self.subTest(apertura=apertura, cierre=cierre):
                response = self.client.post(
                    self.list_url,
                    self._payload(
                        horarios=[
                            {
                                "dia_semana": 1,
                                "hora_apertura": apertura,
                                "hora_cierre": cierre,
                            }
                        ]
                    ),
                    format="json",
                    **self._auth(self.admin_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertEqual(Sede.objects.count(), 0)

    def test_rechaza_dia_semana_fuera_de_rango(self):
        for dia in (0, 8):
            with self.subTest(dia=dia):
                response = self.client.post(
                    self.list_url,
                    self._payload(
                        horarios=[
                            {
                                "dia_semana": dia,
                                "hora_apertura": "08:00:00",
                                "hora_cierre": "12:00:00",
                            }
                        ]
                    ),
                    format="json",
                    **self._auth(self.admin_token),
                )

                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )
                self.assertEqual(Sede.objects.count(), 0)

    def test_rechaza_horarios_traslapados_en_el_mismo_dia(self):
        response = self.client.post(
            self.list_url,
            self._payload(
                horarios=[
                    {
                        "dia_semana": 3,
                        "hora_apertura": "08:00:00",
                        "hora_cierre": "12:00:00",
                    },
                    {
                        "dia_semana": 3,
                        "hora_apertura": "11:00:00",
                        "hora_cierre": "15:00:00",
                    },
                ]
            ),
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Sede.objects.count(), 0)

    def test_consulta_publica_solo_muestra_sedes_activas(self):
        activa = self._crear_sede(nombre="Sede Activa")
        self._crear_sede(nombre="Sede Inactiva", activa=False)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(activa.pk))

    def test_admin_puede_incluir_inactivas_con_parametro(self):
        activa = self._crear_sede(nombre="Sede Activa")
        inactiva = self._crear_sede(nombre="Sede Inactiva", activa=False)

        response = self.client.get(
            self.list_url,
            {"incluir_inactivas": "true"},
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {sede["id"] for sede in response.data},
            {str(activa.pk), str(inactiva.pk)},
        )

        sin_parametro = self.client.get(
            self.list_url, **self._auth(self.admin_token)
        )
        self.assertEqual(len(sin_parametro.data), 1)

    def test_cliente_no_puede_incluir_inactivas(self):
        self._crear_sede(nombre="Sede Activa")
        self._crear_sede(nombre="Sede Inactiva", activa=False)

        response = self.client.get(
            self.list_url,
            {"incluir_inactivas": "true"},
            **self._auth(self.cliente_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_detalle_publico_de_sede_activa(self):
        sede = self._crear_sede()

        response = self.client.get(self._detail_url(sede))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(sede.pk))

    def test_detalle_de_sede_inactiva_solo_visible_para_admin(self):
        sede = self._crear_sede(activa=False)
        url = self._detail_url(sede)

        response_cliente = self.client.get(
            url, **self._auth(self.cliente_token)
        )
        response_admin = self.client.get(
            url, **self._auth(self.admin_token)
        )

        self.assertEqual(
            response_cliente.status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)

    def test_admin_edita_sede_y_reemplaza_horarios(self):
        sede = self._crear_sede()

        response = self.client.patch(
            self._detail_url(sede),
            {
                "nombre": "Sede Renovada",
                "horarios": [
                    {
                        "dia_semana": 5,
                        "hora_apertura": "09:00:00",
                        "hora_cierre": "17:00:00",
                    }
                ],
            },
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.nombre, "Sede Renovada")
        self.assertEqual(sede.horarios.count(), 1)
        self.assertEqual(sede.horarios.get().dia_semana, 5)
        self.assertEqual(response.data["nombre"], "Sede Renovada")

    def test_editar_sin_horarios_conserva_los_actuales(self):
        sede = self._crear_sede()

        response = self.client.patch(
            self._detail_url(sede),
            {"telefono": "3111111111"},
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.telefono, "3111111111")
        self.assertEqual(sede.horarios.count(), 2)

    def test_editar_con_horarios_traslapados_no_modifica_nada(self):
        sede = self._crear_sede()

        response = self.client.patch(
            self._detail_url(sede),
            {
                "nombre": "Nombre que no debe guardarse",
                "horarios": [
                    {
                        "dia_semana": 2,
                        "hora_apertura": "08:00:00",
                        "hora_cierre": "12:00:00",
                    },
                    {
                        "dia_semana": 2,
                        "hora_apertura": "10:00:00",
                        "hora_cierre": "14:00:00",
                    },
                ],
            },
            format="json",
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        sede.refresh_from_db()
        self.assertEqual(sede.nombre, "Sede Norte")
        self.assertEqual(sede.horarios.count(), 2)

    def test_admin_desactiva_sede_sin_borrar_registro(self):
        sede = self._crear_sede()
        pk = sede.pk

        response = self.client.delete(
            self._detail_url(sede), **self._auth(self.admin_token)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)
        self.assertTrue(Sede.objects.filter(pk=pk).exists())
        sede.refresh_from_db()
        self.assertFalse(sede.activa)

    def test_admin_reactiva_sede(self):
        sede = self._crear_sede()
        sede.activa = False
        sede.save(update_fields=["activa"])

        response = self.client.post(
            reverse("sede_reactivar", args=[sede.pk]),
            **self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mensaje", response.data)
        self.assertTrue(response.data["sede"]["activa"])
        sede.refresh_from_db()
        self.assertTrue(sede.activa)

    def test_reactivar_sede_exige_admin_y_sede_existente(self):
        sede = self._crear_sede()
        sede.activa = False
        sede.save(update_fields=["activa"])
        url = reverse("sede_reactivar", args=[sede.pk])

        self.assertEqual(
            self.client.post(url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        usuario = User.objects.create_user(
            negocio=negocio_de_rol(Rol.OPERADOR),
            email="operador.reactivar@example.com",
            password="ClaveSegura#2024",
            nombre="Prueba",
            apellido="Sede",
            telefono="3000000000",
            rol=Rol.OPERADOR,
        )
        self.assertEqual(
            self.client.post(
                url, **self._auth(self._token(usuario))
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        sede.refresh_from_db()
        self.assertFalse(sede.activa)

        self.assertEqual(
            self.client.post(
                reverse("sede_reactivar", args=[uuid4()]),
                **self._auth(self.admin_token),
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_no_admin_recibe_403_en_escritura(self):
        sede = self._crear_sede()
        detalle = self._detail_url(sede)

        for nombre_rol, token in (
            ("cliente", self.cliente_token),
            ("repartidor", self.repartidor_token),
        ):
            for metodo, url in (
                ("post", self.list_url),
                ("put", detalle),
                ("patch", detalle),
                ("delete", detalle),
            ):
                with self.subTest(rol=nombre_rol, metodo=metodo):
                    response = getattr(self.client, metodo)(
                        url,
                        self._payload(),
                        format="json",
                        **self._auth(token),
                    )
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_403_FORBIDDEN,
                    )

    def test_sin_token_recibe_401_en_escritura(self):
        sede = self._crear_sede()
        detalle = self._detail_url(sede)

        for metodo, url in (
            ("post", self.list_url),
            ("put", detalle),
            ("patch", detalle),
            ("delete", detalle),
        ):
            with self.subTest(metodo=metodo):
                response = getattr(self.client, metodo)(
                    url, self._payload(), format="json"
                )
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED
                )


class FeriadoTests(APITestCase):
    """HU-8.9: feriados por negocio que cierran una, varias o todas sus sedes."""

    def setUp(self):
        from apps.core.datos_prueba import (
            auth_prueba,
            crear_usuario_prueba,
            habilitar_sede_para_pedidos,
            producto_en_sede,
        )

        self.auth = auth_prueba
        self.norte = Sede.objects.create(negocio=negocio_prueba(), nombre="Norte", direccion="C1")
        self.sur = Sede.objects.create(negocio=negocio_prueba(), nombre="Sur", direccion="C2")
        for sede in (self.norte, self.sur):
            habilitar_sede_para_pedidos(sede)
        self.admin = crear_usuario_prueba("admin.fer@example.com", Rol.ADMIN)
        self.operador = crear_usuario_prueba("op.fer@example.com", Rol.OPERADOR, sede=self.norte)
        self.cliente = crear_usuario_prueba("cli.fer@example.com", Rol.CLIENTE)
        self.productos = {s.pk: producto_en_sede(s, f"Papas {s.nombre}") for s in (self.norte, self.sur)}
        self.hoy = timezone.localdate()
        self.url = reverse("feriado_list_create")

    def _crear(self, datos, usuario=None):
        return self.client.post(self.url, datos, format="json", **self.auth(usuario or self.admin))

    def _pedir(self, sede, url_nombre="pedido_list_create"):
        return self.client.post(
            reverse(url_nombre),
            {
                "sede_id": str(sede.pk), "tipo": "recoger",
                "detalles": [{"producto_id": str(self.productos[sede.pk].pk), "cantidad": 1}],
            },
            format="json", **self.auth(self.cliente),
        )

    def test_feriado_de_todas_las_sedes_bloquea_pedidos(self):
        respuesta = self._crear({"fecha": str(self.hoy), "nombre": "Día festivo"})
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertTrue(respuesta.data["aplica_a_todas"])

        for sede in (self.norte, self.sur):
            with self.subTest(sede=sede.nombre):
                pedido = self._pedir(sede)
                self.assertEqual(pedido.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(str(pedido.data["detail"]), "Sede cerrada por feriado")

    def test_feriado_de_una_sede_no_cierra_las_demas(self):
        self._crear({"fecha": str(self.hoy), "nombre": "Fiesta local", "sedes_ids": [str(self.norte.pk)]})

        self.assertEqual(str(self._pedir(self.norte).data["detail"]), "Sede cerrada por feriado")
        self.assertEqual(self._pedir(self.sur).status_code, status.HTTP_201_CREATED)

    def test_feriado_de_otro_dia_no_bloquea(self):
        self._crear({"fecha": str(self.hoy + timedelta(days=1)), "nombre": "Mañana"})

        self.assertEqual(self._pedir(self.norte).status_code, status.HTTP_201_CREATED)

    def test_cotizar_avisa_el_feriado(self):
        self._crear({"fecha": str(self.hoy), "nombre": "Hoy"})

        respuesta = self._pedir(self.norte, "pedido_cotizar")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["problemas"], ["Sede cerrada por feriado"])
        self.assertFalse(respuesta.data["puede_confirmar"])

    def test_crud_y_permisos(self):
        creado = self._crear({"fecha": "2026-12-25", "nombre": "Navidad"}).data
        detalle = reverse("feriado_detail", args=[creado["id"]])

        editado = self.client.patch(
            detalle, {"sedes_ids": [str(self.sur.pk)]}, format="json", **self.auth(self.admin)
        )
        self.assertEqual([s["nombre"] for s in editado.data["sedes"]], ["Sur"])

        # El operador consulta pero no crea ni borra.
        self.assertEqual(len(self.client.get(self.url, **self.auth(self.operador)).data), 1)
        self.assertEqual(self._crear({"fecha": "2026-12-31", "nombre": "X"}, self.operador).status_code, 403)
        self.assertEqual(self.client.delete(detalle, **self.auth(self.operador)).status_code, 403)

        self.assertEqual(self.client.delete(detalle, **self.auth(self.admin)).status_code, 200)
        self.assertEqual(self.client.get(self.url, **self.auth(self.admin)).data, [])

    def test_no_usa_sedes_de_otro_negocio(self):
        otra = Sede.objects.create(
            negocio=Negocio.objects.create(nombre="Otro"), nombre="Ajena", direccion="C9"
        )

        respuesta = self._crear({"fecha": str(self.hoy), "nombre": "X", "sedes_ids": [str(otra.pk)]})

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sedes_ids", respuesta.data)
