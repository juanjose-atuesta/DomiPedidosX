"""Correos al cliente por tipo de evento, configurables por negocio (HU-8.10)."""

from decimal import Decimal

from django.core import mail
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
from apps.pedidos.services import cambiar_estado_pedido, crear_pedido, rechazar_pedido
from apps.repartos.services import asignar_repartidor
from apps.sedes.models import Sede
from apps.usuarios.models import Rol

from .models import ConfiguracionCorreos, EstadoEnvio, Notificacion, TipoNotificacion


class CorreosPorEventoTests(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(negocio=negocio_prueba(), nombre="Centro", direccion="C1")
        habilitar_sede_para_pedidos(self.sede)
        self.admin = crear_usuario_prueba("admin.mail@example.com", Rol.ADMIN)
        self.cocina = crear_usuario_prueba("cocina.mail@example.com", Rol.COCINA, sede=self.sede)
        self.repartidor = crear_usuario_prueba(
            "rep.mail@example.com", Rol.REPARTIDOR, sede=self.sede, nombre="Rita"
        )
        self.cliente = crear_usuario_prueba("cliente.mail@example.com", Rol.CLIENTE)
        self.producto = producto_en_sede(self.sede)
        mail.outbox.clear()

    def _pedido(self, cliente=None, tipo="domicilio"):
        with self.captureOnCommitCallbacks(execute=True):
            return crear_pedido(
                sede=self.sede,
                cliente=cliente or self.cliente,
                detalles=[{"producto": self.producto, "cantidad": 1}],
                tipo=tipo,
                direccion_entrega="Calle 5",
                entrega_lat=Decimal(LAT_PRUEBA),
                entrega_lng=Decimal(LNG_PRUEBA),
            )

    def _avanzar(self, pedido, estado):
        with self.captureOnCommitCallbacks(execute=True):
            return cambiar_estado_pedido(pedido.pk, estado=estado, usuario=self.cocina)

    def _desactivar(self, **eventos):
        ConfiguracionCorreos.objects.update_or_create(
            negocio=self.sede.negocio, defaults=eventos
        )

    def _asuntos(self):
        return [m.subject for m in mail.outbox]

    def test_por_defecto_todos_los_eventos_envian_correo(self):
        pedido = self._pedido()
        self._avanzar(pedido, "en_preparacion")
        self._avanzar(pedido, "listo_despacho")
        with self.captureOnCommitCallbacks(execute=True):
            asignar_repartidor(pedido.pk, self.repartidor.pk, asignado_por=self.cocina)
        otro = self._pedido()
        with self.captureOnCommitCallbacks(execute=True):
            rechazar_pedido(otro.pk, usuario=self.cocina, motivo="Sin ingredientes hoy")

        asuntos = self._asuntos()
        self.assertEqual(len(asuntos), 6)
        self.assertTrue(all(m.to == ["cliente.mail@example.com"] for m in mail.outbox))
        self.assertIn(f"Recibimos tu pedido #{pedido.pk} - Negocio de prueba", asuntos)
        self.assertIn(f"Tu pedido #{pedido.pk}: En preparación", asuntos)
        self.assertIn(f"Tu pedido #{pedido.pk} ya tiene repartidor", asuntos)
        self.assertIn(f"Pedido #{otro.pk} cancelado", asuntos)
        self.assertIn("Sin ingredientes hoy", mail.outbox[-1].body)
        self.assertEqual(
            Notificacion.objects.filter(canal="correo", estado_envio=EstadoEnvio.ENVIADO).count(), 6
        )

    def test_confirmacion_desactivada(self):
        self._desactivar(confirmacion=False)

        pedido = self._pedido()
        self._avanzar(pedido, "en_preparacion")

        self.assertEqual(self._asuntos(), [f"Tu pedido #{pedido.pk}: En preparación"])

    def test_cambio_de_estado_desactivado(self):
        self._desactivar(cambio_estado=False)

        pedido = self._pedido()
        self._avanzar(pedido, "en_preparacion")
        self._avanzar(pedido, "listo_despacho")

        self.assertEqual(len(mail.outbox), 1)  # solo la confirmación

    def test_cancelacion_y_asignacion_desactivadas(self):
        self._desactivar(cancelacion=False, asignacion_repartidor=False)
        pedido = self._pedido()
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            rechazar_pedido(pedido.pk, usuario=self.cocina, motivo="Motivo de prueba largo")
        otro = self._pedido()
        self._avanzar(otro, "en_preparacion")
        self._avanzar(otro, "listo_despacho")
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            asignar_repartidor(otro.pk, self.repartidor.pk, asignado_por=self.cocina)

        self.assertEqual(mail.outbox, [])
        self.assertFalse(
            Notificacion.objects.filter(
                tipo__in=[TipoNotificacion.PEDIDO_CANCELADO, TipoNotificacion.REPARTIDOR_ASIGNADO]
            ).exists()
        )

    def test_la_configuracion_es_por_negocio(self):
        from apps.negocios.models import Negocio

        ConfiguracionCorreos.objects.create(
            negocio=Negocio.objects.create(nombre="Otro"), confirmacion=False
        )

        self._pedido()

        self.assertEqual(len(mail.outbox), 1)

    def test_cliente_sin_correo_real_no_recibe(self):
        sin_correo = crear_usuario_prueba(
            "cliente-3101234567@sin-correo.invalid", Rol.CLIENTE
        )

        self._pedido(cliente=sin_correo)

        self.assertEqual(mail.outbox, [])

    def test_si_el_pedido_falla_no_sale_correo(self):
        self.producto.inventario.update(controla_stock=True, stock_actual=0)

        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(Exception):
                crear_pedido(
                    sede=self.sede, cliente=self.cliente,
                    detalles=[{"producto": self.producto, "cantidad": 1}],
                )

        self.assertEqual(mail.outbox, [])


class ConfiguracionCorreosApiTests(APITestCase):
    def setUp(self):
        self.url = reverse("configuracion_correos")
        self.admin = crear_usuario_prueba("admin.cfg@example.com", Rol.ADMIN)

    def test_todos_activos_por_defecto_y_se_editan(self):
        inicial = self.client.get(self.url, **auth_prueba(self.admin))
        self.assertEqual(
            {k: inicial.data[k] for k in ("confirmacion", "cambio_estado", "cancelacion", "asignacion_repartidor")},
            {"confirmacion": True, "cambio_estado": True, "cancelacion": True, "asignacion_repartidor": True},
        )

        respuesta = self.client.patch(
            self.url, {"cambio_estado": False}, format="json", **auth_prueba(self.admin)
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        config = ConfiguracionCorreos.objects.get(negocio=self.admin.negocio)
        self.assertFalse(config.cambio_estado)
        self.assertTrue(config.confirmacion)

    def test_solo_el_admin(self):
        operador = crear_usuario_prueba("op.cfg@example.com", Rol.OPERADOR)
        self.assertEqual(self.client.get(self.url, **auth_prueba(operador)).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 401)
