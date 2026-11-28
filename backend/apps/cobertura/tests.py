"""Zonas de cobertura por radio o polígono (HU-8.4 a HU-8.8)."""

from decimal import Decimal

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_de_rol, negocio_prueba
from apps.negocios.models import Negocio
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import CapacidadFranja
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

"""Tope de pedidos simultáneos por franja horaria (HU-9.2).

Guárdalo como apps/cobertura/tests_capacidad.py (o junto a tus otros tests).
"""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_prueba
from apps.pedidos.capacidad import verificar_capacidad_sede
from apps.pedidos.models import EstadoPedido, Pedido
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import CapacidadFranja

CLAVE = "ClaveSegura#2024"


class CapacidadFranjasTests(APITestCase):
    def setUp(self):
        self.admin = self._usuario("admin.cap@example.com", Rol.ADMIN)
        self.operador = self._usuario("op.cap@example.com", Rol.OPERADOR)
        self.otro_operador = self._usuario("op.cap2@example.com", Rol.OPERADOR)
        self.cliente = self._usuario("cli.cap@example.com", Rol.CLIENTE)
        self.sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Centro", direccion="Calle 1",
            tope_general_pedidos=10,
        )
        self.sede_2 = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Norte", direccion="Calle 2",
            tope_general_pedidos=10,
        )
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)
        SedeUsuario.objects.create(usuario=self.otro_operador, sede=self.sede_2)
        self.url = reverse("capacidad_sede", args=[self.sede.pk])

    def _usuario(self, email, rol):
        return User.objects.create_user(
            negocio=negocio_prueba(), email=email, password=CLAVE,
            nombre="X", apellido="Y", telefono="3000000000", rol=rol,
        )

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _crear(self, datos=None, usuario=None, url=None):
        datos = {"dia_semana": 1, "hora_inicio": "12:00", "max_pedidos_simultaneos": 5, **(datos or {})}
        return self.client.post(url or self.url, datos, format="json", **self._auth(usuario or self.operador))

    def test_operador_define_franja_de_una_hora(self):
        r = self._crear()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(r.data["hora_fin"], "13:00:00")
        self.assertEqual(r.data["max_pedidos_simultaneos"], 5)
        self.assertEqual(CapacidadFranja.objects.get().sede, self.sede)

    def test_franja_de_las_23_termina_al_final_del_dia(self):
        r = self._crear({"hora_inicio": "23:00"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        franja = CapacidadFranja.objects.get()
        self.assertGreater(franja.hora_fin, franja.hora_inicio)

    def test_tope_debe_estar_entre_1_y_el_tope_general(self):
        for tope in (0, -3, 11, "x", None):
            with self.subTest(tope=tope):
                r = self._crear({"max_pedidos_simultaneos": tope})
                self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._crear({"max_pedidos_simultaneos": 10}).status_code, 201)
        self.assertEqual(self._crear({"hora_inicio": "13:00", "max_pedidos_simultaneos": 1}).status_code, 201)

    def test_sin_tope_general_no_se_puede_definir_franja(self):
        Sede.objects.filter(pk=self.sede.pk).update(tope_general_pedidos=None)
        r = self._crear()
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CapacidadFranja.objects.count(), 0)

    def test_la_hora_de_inicio_debe_ser_en_punto(self):
        self.assertEqual(self._crear({"hora_inicio": "12:30"}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_se_repite_la_misma_franja(self):
        self._crear()
        self.assertEqual(self._crear().status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._crear({"dia_semana": 2}).status_code, status.HTTP_201_CREATED)

    def test_operador_solo_maneja_su_sede_y_el_cliente_nada(self):
        self.assertEqual(self._crear(usuario=self.otro_operador).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self._crear(usuario=self.cliente).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self._crear(usuario=self.admin).status_code, status.HTTP_201_CREATED)
        self.assertEqual(CapacidadFranja.objects.count(), 1)

    def test_listar_devuelve_tope_general_y_franjas_ordenadas(self):
        self._crear({"dia_semana": 2, "hora_inicio": "09:00"})
        self._crear({"dia_semana": 1, "hora_inicio": "13:00"})
        self._crear({"dia_semana": 1, "hora_inicio": "12:00"})
        r = self.client.get(self.url, **self._auth(self.operador))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["tope_general"], 10)
        self.assertEqual(
            [(f["dia_semana"], f["hora_inicio"]) for f in r.data["franjas"]],
            [(1, "12:00:00"), (1, "13:00:00"), (2, "09:00:00")],
        )

    def test_editar_tope_y_no_superar_el_general(self):
        franja_id = self._crear().data["id"]
        url = reverse("capacidad_detail", args=[franja_id])
        ok = self.client.patch(url, {"max_pedidos_simultaneos": 8}, format="json", **self._auth(self.operador))
        self.assertEqual(ok.status_code, status.HTTP_200_OK, ok.data)
        self.assertEqual(CapacidadFranja.objects.get().max_pedidos_simultaneos, 8)
        mal = self.client.patch(url, {"max_pedidos_simultaneos": 99}, format="json", **self._auth(self.operador))
        self.assertEqual(mal.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CapacidadFranja.objects.get().max_pedidos_simultaneos, 8)

    def test_otro_operador_no_edita_franja_ajena(self):
        franja_id = self._crear().data["id"]
        url = reverse("capacidad_detail", args=[franja_id])
        r = self.client.patch(url, {"max_pedidos_simultaneos": 2}, format="json", **self._auth(self.otro_operador))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_eliminar_es_logico_y_permite_volver_a_crearla(self):
        franja_id = self._crear().data["id"]
        url = reverse("capacidad_detail", args=[franja_id])
        self.assertEqual(self.client.delete(url, **self._auth(self.operador)).status_code, 200)
        self.assertFalse(CapacidadFranja.objects.get(pk=franja_id).activa)
        self.assertEqual(self.client.delete(url, **self._auth(self.operador)).status_code, 404)
        self.assertEqual(self._crear().status_code, status.HTTP_201_CREATED)

    def test_solo_recibido_y_en_preparacion_cuentan_para_el_tope(self):
        ahora = timezone.localtime()
        self._crear({
            "dia_semana": ahora.isoweekday(),
            "hora_inicio": ahora.strftime("%H:00"),
            "max_pedidos_simultaneos": 2,
        })

        def pedido(estado):
            return Pedido.objects.create(
                sede=self.sede, cliente_nombre="C", cliente_telefono="3000000000",
                tipo="recoger", metodo_pago="efectivo", subtotal=0, total=0, estado=estado,
            )

        pedido(EstadoPedido.RECIBIDO)
        pedido(EstadoPedido.LISTO_DESPACHO)
        pedido(EstadoPedido.CANCELADO)
        capacidad = verificar_capacidad_sede(self.sede, ahora)
        self.assertEqual((capacidad.tope, capacidad.en_curso, capacidad.llena), (2, 1, False))

        pedido(EstadoPedido.EN_PREPARACION)
        self.assertTrue(verificar_capacidad_sede(self.sede, ahora).llena)

    def test_listar_incluye_la_ocupacion_de_la_franja_de_hoy(self):
        ahora = timezone.localtime()
        hoy = ahora.isoweekday()
        self._crear({"dia_semana": hoy, "hora_inicio": ahora.strftime("%H:00"), "max_pedidos_simultaneos": 4})
        self._crear({"dia_semana": hoy % 7 + 1, "hora_inicio": "12:00", "max_pedidos_simultaneos": 4})
        for estado in (EstadoPedido.RECIBIDO, EstadoPedido.EN_PREPARACION, EstadoPedido.ENTREGADO):
            Pedido.objects.create(
                sede=self.sede, cliente_nombre="C", cliente_telefono="3000000000",
                tipo="recoger", metodo_pago="efectivo", subtotal=0, total=0, estado=estado,
            )
        r = self.client.get(self.url, **self._auth(self.operador))
        por_dia = {f["dia_semana"]: f for f in r.data["franjas"]}
        self.assertEqual(por_dia[hoy]["pedidos_actuales"], 2)
        self.assertEqual(por_dia[hoy]["umbral_alerta_pct"], 80)
        self.assertIsNone(por_dia[hoy % 7 + 1]["pedidos_actuales"])
