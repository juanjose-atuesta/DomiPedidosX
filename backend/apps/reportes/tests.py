"""Reporte de ventas por sede y zona (HU-10.5)."""

from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cobertura.models import TipoCobertura, ZonaCobertura
from apps.negocios.models import Negocio
from apps.pedidos.models import EstadoPedido, MetodoPago, Pedido
from apps.sedes.models import Sede
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

CLAVE = "ClaveSegura#2024"
URL = "reporte_ventas_sede_zona"


class ReporteVentasSedeZonaTests(APITestCase):
    def setUp(self):
        self.negocio = Negocio.objects.create(nombre="Negocio A")
        self.admin = self._usuario("admin@example.com", Rol.ADMIN, self.negocio)
        self.centro = Sede.objects.create(negocio=self.negocio, nombre="Centro", direccion="Calle 1")
        self.norte = Sede.objects.create(negocio=self.negocio, nombre="Norte", direccion="Calle 2")
        self.zona_c1 = self._zona(self.centro, "Zona 1")
        self.zona_c2 = self._zona(self.centro, "Zona 2")
        self.zona_n1 = self._zona(self.norte, "Zona 1")

    def _usuario(self, email, rol, negocio):
        return User.objects.create_user(
            email=email, password=CLAVE, nombre="Prueba", apellido=rol,
            telefono="3000000000", rol=rol, negocio=negocio,
        )

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _zona(self, sede, nombre):
        return ZonaCobertura.objects.create(
            sede=sede, nombre=nombre, tipo=TipoCobertura.RADIO, centro_lat=Decimal("3.45"),
            centro_lng=Decimal("-76.53"), radio_km=Decimal("5"), tiempo_estimado_min=30,
        )

    def _pedido(self, sede, zona, total, dia, hora=12, estado=EstadoPedido.ENTREGADO):
        pedido = Pedido.objects.create(
            cliente_nombre="Ana", cliente_telefono="3000000000", sede=sede, zona=zona,
            estado=estado, metodo_pago=MetodoPago.EFECTIVO, subtotal=total, total=total,
            direccion_entrega="Calle 1 # 2-3", entrega_lat=Decimal("3.45"),
            entrega_lng=Decimal("-76.53"),
        )
        momento = timezone.make_aware(datetime(2026, 11, dia, hora, 0))
        Pedido.objects.filter(pk=pedido.pk).update(creado_en=momento)
        return pedido

    def _reporte(self, usuario=None, **parametros):
        return self.client.get(reverse(URL), parametros, **self._auth(usuario or self.admin))

    def _sede(self, respuesta, nombre):
        return next(s for s in respuesta.data["sedes"] if s["sede_nombre"] == nombre)

    def test_suma_pedidos_y_valor_por_sede_y_zona(self):
        self._pedido(self.centro, self.zona_c1, Decimal("10000"), 10)
        self._pedido(self.centro, self.zona_c1, Decimal("5000"), 11)
        self._pedido(self.centro, self.zona_c2, Decimal("7000"), 12)
        self._pedido(self.norte, self.zona_n1, Decimal("3000"), 12)

        r = self._reporte(desde="2026-11-01", hasta="2026-11-30")

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["total_pedidos"], 4)
        self.assertEqual(r.data["total_vendido"], Decimal("25000"))
        centro = self._sede(r, "Centro")
        self.assertEqual(centro["numero_pedidos"], 3)
        self.assertEqual(centro["valor_vendido"], Decimal("22000"))
        zona1 = next(z for z in centro["zonas"] if z["zona_nombre"] == "Zona 1")
        self.assertEqual((zona1["numero_pedidos"], zona1["valor_vendido"]), (2, Decimal("15000")))

    def test_excluye_pedidos_cancelados(self):
        self._pedido(self.centro, self.zona_c1, Decimal("10000"), 10)
        self._pedido(self.centro, self.zona_c1, Decimal("99000"), 10, estado=EstadoPedido.CANCELADO)

        r = self._reporte(desde="2026-11-01", hasta="2026-11-30")

        self.assertEqual(r.data["total_pedidos"], 1)
        self.assertEqual(r.data["total_vendido"], Decimal("10000"))

    def test_el_periodo_incluye_los_dos_dias_limite_y_deja_fuera_el_resto(self):
        self._pedido(self.centro, self.zona_c1, Decimal("1000"), 9, hora=23)
        self._pedido(self.centro, self.zona_c1, Decimal("2000"), 10, hora=0)
        self._pedido(self.centro, self.zona_c1, Decimal("4000"), 12, hora=23)
        self._pedido(self.centro, self.zona_c1, Decimal("8000"), 13, hora=1)

        r = self._reporte(desde="2026-11-10", hasta="2026-11-12")

        self.assertEqual(r.data["total_vendido"], Decimal("6000"))

    def test_lista_sedes_y_zonas_sin_ventas_con_cero(self):
        r = self._reporte(desde="2026-11-01", hasta="2026-11-30")

        self.assertEqual([s["sede_nombre"] for s in r.data["sedes"]], ["Centro", "Norte"])
        centro = self._sede(r, "Centro")
        self.assertEqual([z["zona_nombre"] for z in centro["zonas"]], ["Zona 1", "Zona 2"])
        self.assertEqual(centro["zonas"][0]["numero_pedidos"], 0)
        self.assertEqual(centro["zonas"][0]["valor_vendido"], Decimal("0"))

    def test_agrupa_aparte_los_pedidos_sin_zona(self):
        self._pedido(self.centro, None, Decimal("6000"), 10)

        r = self._reporte(desde="2026-11-01", hasta="2026-11-30")

        centro = self._sede(r, "Centro")
        sin_zona = next(z for z in centro["zonas"] if z["zona_nombre"] == "Sin zona")
        self.assertEqual((sin_zona["numero_pedidos"], sin_zona["valor_vendido"]), (1, Decimal("6000")))
        self.assertEqual(centro["valor_vendido"], Decimal("6000"))

    def test_no_incluye_datos_de_otro_negocio(self):
        otro = Negocio.objects.create(nombre="Negocio B")
        sede_b = Sede.objects.create(negocio=otro, nombre="Sede B", direccion="Calle 9")
        self._pedido(sede_b, self._zona(sede_b, "Zona B"), Decimal("50000"), 10)

        r = self._reporte(desde="2026-11-01", hasta="2026-11-30")

        self.assertEqual(r.data["total_pedidos"], 0)
        self.assertNotIn("Sede B", [s["sede_nombre"] for s in r.data["sedes"]])

    def test_exige_fechas_de_inicio_y_fin(self):
        r = self._reporte(desde="2026-11-01")

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("hasta", r.data)

    def test_rechaza_inicio_posterior_al_fin(self):
        r = self._reporte(desde="2026-11-20", hasta="2026-11-10")

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_solo_el_admin_puede_generar_el_reporte(self):
        operador = self._usuario("op@example.com", Rol.OPERADOR, self.negocio)

        r = self._reporte(operador, desde="2026-11-01", hasta="2026-11-30")

        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        sin_sesion = self.client.get(reverse(URL), {"desde": "2026-11-01", "hasta": "2026-11-30"})
        self.assertEqual(sin_sesion.status_code, status.HTTP_401_UNAUTHORIZED)
