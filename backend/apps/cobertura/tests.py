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
PASSWORD = "ClaveSegura#2024"
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

"""Pruebas de HU-9.2: tope de pedidos simultáneos por franja horaria."""
TOPE_GENERAL = 10


class CapacidadFranjaTests(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Norte", direccion="Calle 1",
            tope_general_pedidos=TOPE_GENERAL,
        )
        self.otra_sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Sur", direccion="Calle 2",
            tope_general_pedidos=TOPE_GENERAL,
        )
        self.sede_sin_tope = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Nueva", direccion="Calle 3",
            tope_general_pedidos=None,
        )
        self.admin = self._crear("admin.cap@example.com", Rol.ADMIN)
        self.operador = self._crear("op.cap@example.com", Rol.OPERADOR)
        self.operador_otra = self._crear("op.otra@example.com", Rol.OPERADOR)
        self.cocina = self._crear("cocina.cap@example.com", Rol.COCINA)
        self.cliente = User.objects.create_user(
            email="cliente.cap@example.com", password=PASSWORD, nombre="Ana",
            apellido="Cliente", telefono="3000000000",
        )
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)
        SedeUsuario.objects.create(usuario=self.operador_otra, sede=self.otra_sede)
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede_sin_tope)
        self.url = reverse("capacidad_sede", args=[self.sede.pk])

    # --- ayudantes -------------------------------------------------------
    def _crear(self, email, rol):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol), email=email, password=PASSWORD,
            nombre="Prueba", apellido="Capacidad", telefono="3000000000", rol=rol,
        )

    def _auth(self, usuario=None):
        token = LoginSerializer.get_token(usuario or self.operador).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload(self, **overrides):
        data = {"dia_semana": 1, "hora_inicio": "12:00", "max_pedidos_simultaneos": 5}
        data.update(overrides)
        return data

    def _post(self, payload=None, usuario=None, url=None):
        return self.client.post(
            url or self.url, payload or self._payload(), format="json",
            **self._auth(usuario),
        )

    def _crear_franja(self, **overrides):
        respuesta = self._post(self._payload(**overrides))
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        return respuesta.data

    def _detalle(self, franja):
        return reverse("capacidad_detail", args=[franja["id"]])

    # --- criterio 1: franjas de 1 hora ----------------------------------
    def test_crea_franja_y_el_servidor_calcula_hora_fin(self):
        respuesta = self._post(self._payload(hora_fin="20:00"))  # se ignora

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["hora_inicio"], "12:00:00")
        self.assertEqual(respuesta.data["hora_fin"], "13:00:00")
        self.assertEqual(respuesta.data["sede_id"], str(self.sede.pk))
        self.assertTrue(respuesta.data["activa"])

    def test_franja_de_las_23_termina_al_final_del_dia(self):
        respuesta = self._post(self._payload(hora_inicio="23:00"))

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(respuesta.data["hora_fin"].startswith("23:59:59"))

    def test_hora_de_inicio_debe_ser_en_punto(self):
        for hora in ("12:30", "12:01", "12:00:30"):
            with self.subTest(hora=hora):
                respuesta = self._post(self._payload(hora_inicio=hora))
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("hora_inicio", respuesta.data)
        self.assertEqual(CapacidadFranja.objects.count(), 0)

    # --- criterio 2: tope entre 1 y el tope general ---------------------
    def test_tope_menor_a_1_da_400(self):
        for tope in (0, -3):
            with self.subTest(tope=tope):
                respuesta = self._post(self._payload(max_pedidos_simultaneos=tope))
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("max_pedidos_simultaneos", respuesta.data)

    def test_tope_no_entero_da_400(self):
        for tope in ("abc", None):
            with self.subTest(tope=tope):
                respuesta = self._post(self._payload(max_pedidos_simultaneos=tope))
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_limites_validos_1_y_tope_general(self):
        self._crear_franja(hora_inicio="10:00", max_pedidos_simultaneos=1)
        self._crear_franja(hora_inicio="11:00", max_pedidos_simultaneos=TOPE_GENERAL)

    def test_tope_mayor_al_general_da_400(self):
        respuesta = self._post(self._payload(max_pedidos_simultaneos=TOPE_GENERAL + 1))

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_pedidos_simultaneos", respuesta.data)
        self.assertIn(str(TOPE_GENERAL), str(respuesta.data["max_pedidos_simultaneos"]))

    def test_sede_sin_tope_general_da_400(self):
        url = reverse("capacidad_sede", args=[self.sede_sin_tope.pk])

        respuesta = self._post(url=url)

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_pedidos_simultaneos", respuesta.data)

    # --- duplicados -------------------------------------------------------
    def test_no_repite_franja_activa_del_mismo_dia_y_hora(self):
        self._crear_franja()

        repetida = self._post()
        otro_dia = self._post(self._payload(dia_semana=2))
        otra_hora = self._post(self._payload(hora_inicio="13:00"))

        self.assertEqual(repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(otro_dia.status_code, status.HTTP_201_CREATED)
        self.assertEqual(otra_hora.status_code, status.HTTP_201_CREATED)

    def test_misma_franja_en_otra_sede_si_se_permite(self):
        self._crear_franja()
        url = reverse("capacidad_sede", args=[self.otra_sede.pk])

        respuesta = self._post(url=url, usuario=self.operador_otra)

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    # --- listado ----------------------------------------------------------
    def test_listado_solo_activas_y_ordenadas(self):
        tarde = self._crear_franja(hora_inicio="18:00")
        self._crear_franja(hora_inicio="12:00")
        self._crear_franja(dia_semana=2, hora_inicio="09:00")
        self.client.delete(self._detalle(tarde), **self._auth())

        respuesta = self.client.get(self.url, **self._auth())

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["tope_general"], TOPE_GENERAL)
        self.assertEqual(
            [(f["dia_semana"], f["hora_inicio"]) for f in respuesta.data["franjas"]],
            [(1, "12:00:00"), (2, "09:00:00")],
        )

    # --- edición ----------------------------------------------------------
    def test_patch_cambia_el_tope(self):
        franja = self._crear_franja()

        respuesta = self.client.patch(
            self._detalle(franja), {"max_pedidos_simultaneos": 8},
            format="json", **self._auth(),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["max_pedidos_simultaneos"], 8)
        self.assertEqual(respuesta.data["hora_fin"], "13:00:00")

    def test_patch_con_tope_mayor_al_general_da_400(self):
        franja = self._crear_franja()

        respuesta = self.client.patch(
            self._detalle(franja), {"max_pedidos_simultaneos": TOPE_GENERAL + 1},
            format="json", **self._auth(),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            CapacidadFranja.objects.get(pk=franja["id"]).max_pedidos_simultaneos, 5
        )

    def test_patch_de_hora_recalcula_hora_fin(self):
        franja = self._crear_franja()

        respuesta = self.client.patch(
            self._detalle(franja), {"hora_inicio": "14:00"},
            format="json", **self._auth(),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["hora_fin"], "15:00:00")

    def test_put_actualiza_la_franja_completa(self):
        franja = self._crear_franja()

        respuesta = self.client.put(
            self._detalle(franja),
            self._payload(dia_semana=3, hora_inicio="19:00", max_pedidos_simultaneos=7),
            format="json", **self._auth(),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["dia_semana"], 3)
        self.assertEqual(respuesta.data["hora_fin"], "20:00:00")

    def test_patch_no_puede_chocar_con_otra_franja(self):
        self._crear_franja(hora_inicio="12:00")
        otra = self._crear_franja(hora_inicio="13:00")

        respuesta = self.client.patch(
            self._detalle(otra), {"hora_inicio": "12:00"}, format="json", **self._auth(),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    # --- borrado lógico ---------------------------------------------------
    def test_delete_es_logico_y_se_puede_volver_a_crear(self):
        franja = self._crear_franja()

        respuesta = self.client.delete(self._detalle(franja), **self._auth())

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(CapacidadFranja.objects.get(pk=franja["id"]).activa)
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)
        # La franja eliminada ya no se puede editar ni eliminar de nuevo.
        self.assertEqual(
            self.client.delete(self._detalle(franja), **self._auth()).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_franja_inexistente_da_404(self):
        url = reverse("capacidad_detail", args=[999999])
        self.assertEqual(
            self.client.patch(url, {}, format="json", **self._auth()).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --- permisos ---------------------------------------------------------
    def test_admin_define_franjas_en_cualquier_sede_de_su_negocio(self):
        url = reverse("capacidad_sede", args=[self.otra_sede.pk])

        respuesta = self._post(url=url, usuario=self.admin)

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_operador_de_otra_sede_no_puede(self):
        franja = self._crear_franja()

        respuestas = [
            self._post(usuario=self.operador_otra),
            self.client.get(self.url, **self._auth(self.operador_otra)),
            self.client.patch(
                self._detalle(franja), {"max_pedidos_simultaneos": 2},
                format="json", **self._auth(self.operador_otra),
            ),
            self.client.delete(self._detalle(franja), **self._auth(self.operador_otra)),
        ]

        for respuesta in respuestas:
            # Ajusta al código que devuelva exigir_operacion_sede (403 o 404).
            self.assertIn(
                respuesta.status_code,
                (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
            )
        self.assertEqual(CapacidadFranja.objects.filter(sede=self.sede).count(), 1)
        self.assertTrue(CapacidadFranja.objects.get(pk=franja["id"]).activa)

    def test_cocina_y_cliente_no_acceden(self):
        for usuario in (self.cocina, self.cliente):
            with self.subTest(rol=usuario.rol):
                self.assertEqual(
                    self.client.get(self.url, **self._auth(usuario)).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self._post(usuario=usuario).status_code, status.HTTP_403_FORBIDDEN
                )

    def test_sin_token_da_401(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.post(self.url, self._payload(), format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_sede_inexistente_da_404(self):
        url = reverse("capacidad_sede", args=["00000000-0000-0000-0000-000000000000"])
        self.assertEqual(
            self.client.get(url, **self._auth(self.admin)).status_code,
            status.HTTP_404_NOT_FOUND,
        )