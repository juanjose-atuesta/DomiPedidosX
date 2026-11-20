"""Asignación de repartidores: manual (HU-6.5) y automática por menor carga (HU-6.6)."""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import (
    LAT_PRUEBA,
    LNG_PRUEBA,
    auth_prueba,
    crear_usuario_prueba,
    habilitar_sede_para_pedidos,
    negocio_prueba,
    producto_en_sede,
)
from apps.notificaciones.models import Notificacion, TipoNotificacion
from apps.pedidos.models import EstadoPedido, HistorialEstado, Pedido
from apps.pedidos.services import cambiar_estado_pedido, crear_pedido
from apps.sedes.models import Sede
from apps.usuarios.models import PerfilRepartidor, Rol


class _BaseReparto(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Centro", direccion="Calle 1"
        )
        habilitar_sede_para_pedidos(self.sede)
        self.otra_sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Sur", direccion="Calle 9"
        )
        habilitar_sede_para_pedidos(self.otra_sede)
        self.operador = crear_usuario_prueba("op@example.com", Rol.OPERADOR, sede=self.sede)
        self.cocina = crear_usuario_prueba("cocina@example.com", Rol.COCINA, sede=self.sede)
        self.ana = crear_usuario_prueba("ana@example.com", Rol.REPARTIDOR, sede=self.sede, nombre="Ana")
        self.beto = crear_usuario_prueba("beto@example.com", Rol.REPARTIDOR, sede=self.sede, nombre="Beto")
        self.ajeno = crear_usuario_prueba("ajeno@example.com", Rol.REPARTIDOR, sede=self.otra_sede, nombre="Ajeno")
        self.producto = producto_en_sede(self.sede)

    def _pedido(self, estado=EstadoPedido.LISTO_DESPACHO, sede=None):
        """Domicilio que llega al estado indicado pasando por el flujo real."""
        sede = sede or self.sede
        producto = self.producto if sede == self.sede else producto_en_sede(sede, "Otro")
        pedido = crear_pedido(
            sede=sede,
            detalles=[{"producto": producto, "cantidad": 1}],
            cliente_nombre="Cliente",
            tipo="domicilio",
            direccion_entrega="Calle 5",
            entrega_lat=Decimal(LAT_PRUEBA),
            entrega_lng=Decimal(LNG_PRUEBA),
        )
        for siguiente in (EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO_DESPACHO):
            if pedido.estado == estado:
                break
            pedido = cambiar_estado_pedido(pedido.pk, estado=siguiente, usuario=self.cocina)
        pedido.refresh_from_db()
        return pedido

    def _asignar(self, pedido, repartidor, usuario=None):
        return self.client.post(
            reverse("asignar_repartidor", args=[pedido.pk]),
            {"repartidor_id": str(repartidor.pk)},
            format="json",
            **auth_prueba(usuario or self.operador),
        )

    def _disponible(self, repartidor):
        return PerfilRepartidor.objects.get(usuario=repartidor).disponible

    def _avanzar(self, pedido, estado, usuario):
        return self.client.patch(
            reverse("pedido_estado", args=[pedido.pk]),
            {"estado": estado},
            format="json",
            **auth_prueba(usuario),
        )


class AsignacionManualTests(_BaseReparto):
    def test_lista_repartidores_de_la_sede_con_su_estado(self):
        PerfilRepartidor.objects.filter(usuario=self.beto).update(disponible=False)

        respuesta = self.client.get(
            reverse("repartidores_sede", args=[self.sede.pk]), **auth_prueba(self.operador)
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        estados = {r["nombre"]: r["estado"] for r in respuesta.data["repartidores"]}
        self.assertEqual(estados, {"Ana": "disponible", "Beto": "ocupado"})  # sin "Ajeno"

    def test_asignar_disponible_lo_marca_ocupado(self):
        pedido = self._pedido()

        respuesta = self._asignar(pedido, self.ana)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data["repartidor_nombre"], "Ana Prueba")
        self.assertFalse(respuesta.data["esperando_repartidor"])
        pedido.refresh_from_db()
        self.assertEqual(pedido.repartidor, self.ana)
        self.assertFalse(self._disponible(self.ana))
        self.assertIn(
            "asignado manualmente",
            HistorialEstado.objects.filter(pedido=pedido).last().comentario,
        )
        # Solo Ana lo ve entre sus entregas; Beto ya no.
        ids_beto = {
            p["id"]
            for p in self.client.get(reverse("pedido_list_create"), **auth_prueba(self.beto)).data
        }
        self.assertNotIn(pedido.pk, ids_beto)

    def test_no_asigna_repartidor_ocupado_ni_de_otra_sede(self):
        PerfilRepartidor.objects.filter(usuario=self.beto).update(disponible=False)
        pedido = self._pedido()

        ocupado = self._asignar(pedido, self.beto)
        ajeno = self._asignar(pedido, self.ajeno)

        self.assertEqual(ocupado.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ocupado", ocupado.data["detail"])
        self.assertEqual(ajeno.status_code, status.HTTP_400_BAD_REQUEST)
        pedido.refresh_from_db()
        self.assertIsNone(pedido.repartidor)

    def test_solo_pedidos_listos_para_despacho(self):
        pedido = self._pedido(EstadoPedido.EN_PREPARACION)

        respuesta = self._asignar(pedido, self.ana)

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self._disponible(self.ana))

    def test_al_entregar_el_repartidor_vuelve_a_disponible(self):
        pedido = self._pedido()
        self._asignar(pedido, self.ana)

        self.assertEqual(self._avanzar(pedido, "en_camino", self.ana).status_code, 200)
        self.assertFalse(self._disponible(self.ana))
        self.assertEqual(self._avanzar(pedido, "entregado", self.ana).status_code, 200)

        self.assertTrue(self._disponible(self.ana))

    def test_reasignar_libera_al_anterior(self):
        pedido = self._pedido()
        self._asignar(pedido, self.ana)

        self.assertEqual(self._asignar(pedido, self.beto).status_code, 200)

        self.assertTrue(self._disponible(self.ana))
        self.assertFalse(self._disponible(self.beto))

    def test_repartidor_que_toma_un_pedido_queda_ocupado(self):
        pedido = self._pedido()

        self._avanzar(pedido, "en_camino", self.beto)

        self.assertFalse(self._disponible(self.beto))

    def test_otro_operador_o_cocina_no_asignan(self):
        pedido = self._pedido()
        operador_sur = crear_usuario_prueba("op.sur@example.com", Rol.OPERADOR, sede=self.otra_sede)

        self.assertEqual(self._asignar(pedido, self.ana, operador_sur).status_code, 403)
        self.assertEqual(self._asignar(pedido, self.ana, self.cocina).status_code, 403)


class AsignacionAutomaticaTests(_BaseReparto):
    def setUp(self):
        super().setUp()
        self.sede.asignacion_automatica_repartidor = True
        self.sede.save()
        self.carlos = crear_usuario_prueba(
            "carlos@example.com", Rol.REPARTIDOR, sede=self.sede, nombre="Carlos"
        )

    def _cargar(self, repartidor, cantidad):
        """Le suma `cantidad` pedidos ya entregados hoy."""
        for _ in range(cantidad):
            pedido = self._pedido(EstadoPedido.EN_PREPARACION)
            Pedido.objects.filter(pk=pedido.pk).update(
                repartidor=repartidor, estado=EstadoPedido.ENTREGADO
            )

    def test_elige_al_disponible_con_menos_pedidos_del_dia(self):
        self._cargar(self.ana, 2)
        self._cargar(self.beto, 1)
        # Carlos no tiene pedidos, pero está ocupado: no cuenta.
        PerfilRepartidor.objects.filter(usuario=self.carlos).update(disponible=False)

        pedido = self._pedido()

        self.assertEqual(pedido.repartidor, self.beto)
        self.assertFalse(self._disponible(self.beto))
        self.assertIn(
            "asignado automáticamente",
            HistorialEstado.objects.filter(pedido=pedido).last().comentario,
        )

    def test_los_cancelados_no_cuentan_como_carga(self):
        self._cargar(self.ana, 1)
        self._cargar(self.carlos, 1)
        for _ in range(3):
            pedido = self._pedido(EstadoPedido.EN_PREPARACION)
            Pedido.objects.filter(pk=pedido.pk).update(
                repartidor=self.beto, estado=EstadoPedido.CANCELADO
            )

        self.assertEqual(self._pedido().repartidor, self.beto)

    def test_sin_disponibles_queda_pendiente_con_alerta(self):
        PerfilRepartidor.objects.filter(usuario__rol=Rol.REPARTIDOR).update(disponible=False)

        pedido = self._pedido()

        self.assertIsNone(pedido.repartidor)
        alerta = Notificacion.objects.get(tipo=TipoNotificacion.SIN_REPARTIDOR)
        self.assertEqual(alerta.pedido, pedido)
        datos = self.client.get(reverse("pedido_list_create"), **auth_prueba(self.operador)).data
        self.assertTrue(next(p for p in datos if p["id"] == pedido.pk)["esperando_repartidor"])

    def test_al_liberarse_un_repartidor_toma_el_pendiente(self):
        PerfilRepartidor.objects.filter(usuario__in=[self.beto, self.carlos]).update(disponible=False)
        primero = self._pedido()
        self.assertEqual(primero.repartidor, self.ana)
        pendiente = self._pedido()
        self.assertIsNone(pendiente.repartidor)

        self._avanzar(primero, "en_camino", self.ana)
        self._avanzar(primero, "entregado", self.ana)

        pendiente.refresh_from_db()
        self.assertEqual(pendiente.repartidor, self.ana)
        self.assertFalse(self._disponible(self.ana))

    def test_sin_la_opcion_activa_no_asigna(self):
        self.sede.asignacion_automatica_repartidor = False
        self.sede.save()

        self.assertIsNone(self._pedido().repartidor)

    def test_el_interruptor_reparte_los_que_esperaban(self):
        self.sede.asignacion_automatica_repartidor = False
        self.sede.save()
        pedido = self._pedido()

        respuesta = self.client.patch(
            reverse("configuracion_reparto", args=[self.sede.pk]),
            {"asignacion_automatica_repartidor": True},
            format="json",
            **auth_prueba(self.operador),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.sede.refresh_from_db()
        self.assertTrue(self.sede.asignacion_automatica_repartidor)
        pedido.refresh_from_db()
        self.assertIsNotNone(pedido.repartidor)

    def test_recoger_en_sede_no_lleva_repartidor(self):
        pedido = crear_pedido(
            sede=self.sede, detalles=[{"producto": self.producto, "cantidad": 1}], tipo="recoger"
        )
        cambiar_estado_pedido(pedido.pk, estado="en_preparacion", usuario=self.cocina)
        pedido = cambiar_estado_pedido(pedido.pk, estado="listo_despacho", usuario=self.cocina)

        self.assertIsNone(pedido.repartidor)
