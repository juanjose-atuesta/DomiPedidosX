"""Zonas de cobertura por radio o polígono (HU-8.4 a HU-8.8)."""

from decimal import Decimal

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_prueba
from apps.negocios.models import Negocio
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import ZonaCobertura
from .services import distancia_km, normalizar_poligono, punto_en_poligono

CLAVE = "ClaveSegura#2024"
# Cuadrado de ~1,1 km de lado alrededor del centro de Cali.
CUADRADO = [[3.44, -76.54], [3.44, -76.53], [3.45, -76.53], [3.45, -76.54]]


class GeometriaTests(SimpleTestCase):
    def test_distancia_haversine(self):
        # Un grado de latitud son ~111,2 km.
        self.assertAlmostEqual(distancia_km(3, -76, 4, -76), 111.2, delta=0.2)
        self.assertEqual(distancia_km(3.45, -76.53, 3.45, -76.53), 0)

    def test_punto_dentro_fuera_y_en_el_borde_del_poligono(self):
        self.assertTrue(punto_en_poligono(3.445, -76.535, CUADRADO))
        self.assertFalse(punto_en_poligono(3.46, -76.535, CUADRADO))
        self.assertFalse(punto_en_poligono(3.445, -76.52, CUADRADO))
        self.assertTrue(punto_en_poligono(3.44, -76.535, CUADRADO))  # borde

    def test_poligono_concavo(self):
        # Forma de "U": el hueco del medio no está cubierto.
        u = [[0, 0], [0, 3], [3, 3], [3, 2], [1, 2], [1, 1], [3, 1], [3, 0]]
        self.assertTrue(punto_en_poligono(0.5, 1.5, u))
        self.assertFalse(punto_en_poligono(2, 1.5, u))

    def test_poligono_necesita_tres_puntos_distintos(self):
        with self.assertRaises(ValueError):
            normalizar_poligono([[3.44, -76.54], [3.45, -76.53]])
        with self.assertRaises(ValueError):  # cerrado, pero solo 2 distintos
            normalizar_poligono([[3.44, -76.54], [3.45, -76.53], [3.44, -76.54]])
        with self.assertRaises(ValueError):
            normalizar_poligono([[95, -76.54], [3.45, -76.53], [3.44, -76.5]])
        self.assertEqual(len(normalizar_poligono(CUADRADO + [CUADRADO[0]])), 4)


class ZonasApiTests(APITestCase):
    def setUp(self):
        self.admin = self._usuario("admin.zonas@example.com", Rol.ADMIN)
        self.operador = self._usuario("op.zonas@example.com", Rol.OPERADOR)
        self.sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Centro", direccion="Calle 1"
        )
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)
        self.url = reverse("zonas_sede", args=[self.sede.pk])

    def _usuario(self, email, rol, negocio=None):
        return User.objects.create_user(
            negocio=negocio or negocio_prueba(), email=email, password=CLAVE,
            nombre="X", apellido="Y", telefono="3000000000", rol=rol,
        )

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _crear(self, datos, usuario=None):
        return self.client.post(
            self.url, datos, format="json", **self._auth(usuario or self.admin)
        )

    def _radio(self, **extra):
        return {
            "nombre": "Centro 3 km", "tipo": "radio", "centro_lat": "3.45",
            "centro_lng": "-76.53", "radio_km": "3", "tarifa_domicilio": "4000",
            "pedido_minimo": "20000", "tiempo_estimado_min": 35, **extra,
        }

    def test_admin_crea_zona_por_radio_y_por_poligono(self):
        radio = self._crear(self._radio())
        poligono = self._crear(
            {
                "nombre": "Cuadrante", "tipo": "poligono", "poligono": CUADRADO,
                "tarifa_domicilio": "3000", "tiempo_estimado_min": 25,
            }
        )

        self.assertEqual(radio.status_code, status.HTTP_201_CREATED, radio.data)
        self.assertEqual(radio.data["tarifa_domicilio"], "4000.00")
        self.assertEqual(poligono.status_code, status.HTTP_201_CREATED, poligono.data)
        self.assertEqual(len(poligono.data["poligono"]), 4)
        self.assertIsNone(poligono.data["radio_km"])

    def test_geometria_incompleta_da_400(self):
        casos = [
            self._radio(radio_km=None),
            self._radio(radio_km="0"),
            self._radio(centro_lat=None),
            {**self._radio(), "tipo": "poligono", "poligono": CUADRADO[:2]},
            self._radio(tarifa_domicilio="-1"),
        ]
        for datos in casos:
            with self.subTest(datos=datos):
                self.assertEqual(
                    self._crear(datos).status_code, status.HTTP_400_BAD_REQUEST
                )
        self.assertEqual(ZonaCobertura.objects.count(), 0)

    def test_editar_cambia_de_radio_a_poligono_y_borrar_desactiva(self):
        zona_id = self._crear(self._radio()).data["id"]
        url = reverse("zona_detail", args=[zona_id])

        respuesta = self.client.patch(
            url, {"tipo": "poligono", "poligono": CUADRADO}, format="json",
            **self._auth(self.admin),
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertIsNone(respuesta.data["centro_lat"])

        self.client.delete(url, **self._auth(self.admin))
        self.assertFalse(ZonaCobertura.objects.get(pk=zona_id).activa)

    def test_operador_consulta_pero_no_crea(self):
        self._crear(self._radio())
        self.assertEqual(
            self._crear(self._radio(), self.operador).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        respuesta = self.client.get(self.url, **self._auth(self.operador))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 1)

    def test_admin_de_otro_negocio_no_ve_la_sede(self):
        otro = self._usuario(
            "admin.otro@example.com", Rol.ADMIN, Negocio.objects.create(nombre="Otro")
        )
        self.assertEqual(
            self._crear(self._radio(), otro).status_code, status.HTTP_404_NOT_FOUND
        )

    def test_verificar_cobertura_es_publico(self):
        self._crear(self._radio())
        url = reverse("verificar_cobertura")

        dentro = self.client.get(url, {"lat": "3.46", "lng": "-76.53"})
        fuera = self.client.get(url, {"lat": "3.6", "lng": "-76.53"})

        self.assertTrue(dentro.data["cubierta"])
        self.assertEqual(dentro.data["zonas"][0]["tarifa_domicilio"], "4000.00")
        self.assertFalse(fuera.data["cubierta"])
        self.assertEqual(
            self.client.get(url, {"lat": "x"}).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_zona_inactiva_o_sede_inactiva_no_cubren(self):
        zona = ZonaCobertura.objects.create(
            sede=self.sede, nombre="Z", tipo="radio", centro_lat=Decimal("3.45"),
            centro_lng=Decimal("-76.53"), radio_km=Decimal("3"), tiempo_estimado_min=30,
        )
        url = reverse("verificar_cobertura")
        punto = {"lat": "3.45", "lng": "-76.53"}
        self.assertTrue(self.client.get(url, punto).data["cubierta"])

        zona.activa = False
        zona.save()
        self.assertFalse(self.client.get(url, punto).data["cubierta"])

        zona.activa = True
        zona.save()
        Sede.objects.filter(pk=self.sede.pk).update(activa=False)
        self.assertFalse(self.client.get(url, punto).data["cubierta"])
