from datetime import time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
