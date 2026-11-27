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


class NotificacionCancelacionOperadorTests(APITestCase):
    """HU-7.5: el operador recibe una alerta cuando el cliente cancela."""

    def setUp(self):
        self.sede = Sede.objects.create(negocio=negocio_prueba(), nombre="Centro", direccion="C1")
        self.otra_sede = Sede.objects.create(negocio=negocio_prueba(), nombre="Norte", direccion="N1")
        habilitar_sede_para_pedidos(self.sede)
        self.operador = crear_usuario_prueba("op.cancel@example.com", Rol.OPERADOR, sede=self.sede)
        self.operador_otra = crear_usuario_prueba(
            "op.norte@example.com", Rol.OPERADOR, sede=self.otra_sede
        )
        self.admin = crear_usuario_prueba("admin.cancel@example.com", Rol.ADMIN)
        self.cliente = crear_usuario_prueba("cli.cancel@example.com", Rol.CLIENTE)
        self.producto = producto_en_sede(self.sede)
        self.url = reverse("notificacion_list")

    def _pedido(self):
        return crear_pedido(
            sede=self.sede,
            cliente=self.cliente,
            detalles=[{"producto": self.producto, "cantidad": 1}],
        )

    def _cancelar(self, pedido, motivo="Me equivoqué de dirección"):
        return self.client.post(
            reverse("pedido_cancelar", args=[pedido.pk]),
            {"motivo": motivo},
            format="json",
            **auth_prueba(self.cliente),
        )

    def _alertas(self):
        return Notificacion.objects.filter(
            tipo=TipoNotificacion.PEDIDO_CANCELADO, canal="sistema"
        )

    def test_cancelar_crea_alerta_para_la_sede_con_numero_y_hora(self):
        from django.utils import timezone

        pedido = self._pedido()

        respuesta = self._cancelar(pedido)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        alerta = self._alertas().get()
        pedido.refresh_from_db()
        hora = timezone.localtime(pedido.actualizado_en)
        self.assertEqual(alerta.sede, self.sede)
        self.assertEqual(alerta.pedido, pedido)
        self.assertIsNone(alerta.usuario)
        self.assertFalse(alerta.leida)
        self.assertIn(f"#{pedido.pk}", alerta.asunto)
        self.assertIn(f"#{pedido.pk}", alerta.mensaje)
        self.assertIn(f"{hora:%H:%M:%S}", alerta.mensaje)
        self.assertIn("Me equivoqué de dirección", alerta.mensaje)

    def test_el_rechazo_de_la_sede_no_genera_alerta_al_operador(self):
        pedido = self._pedido()

        rechazar_pedido(pedido.pk, usuario=self.operador, motivo="Sin ingredientes hoy")

        self.assertFalse(self._alertas().exists())

    def test_cancelacion_fallida_no_genera_alerta(self):
        pedido = self._pedido()
        cambiar_estado_pedido(pedido.pk, estado="en_preparacion", usuario=self.operador)

        respuesta = self._cancelar(pedido)

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self._alertas().exists())

    def test_operador_lista_alertas_de_su_sede(self):
        pedido = self._pedido()
        self._cancelar(pedido)

        respuesta = self.client.get(self.url, **auth_prueba(self.operador))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["no_leidas"], 1)
        self.assertEqual(len(respuesta.data["resultados"]), 1)
        alerta = respuesta.data["resultados"][0]
        self.assertEqual(alerta["pedido_id"], pedido.pk)
        self.assertEqual(alerta["tipo"], "pedido_cancelado")
        self.assertEqual(alerta["sede_nombre"], "Centro")

    def test_operador_de_otra_sede_no_ve_la_alerta(self):
        self._cancelar(self._pedido())

        respuesta = self.client.get(self.url, **auth_prueba(self.operador_otra))

        self.assertEqual(respuesta.data["no_leidas"], 0)
        self.assertEqual(respuesta.data["resultados"], [])

    def test_admin_ve_las_alertas_de_su_negocio_y_filtra_por_sede(self):
        self._cancelar(self._pedido())

        todas = self.client.get(self.url, **auth_prueba(self.admin))
        de_otra = self.client.get(
            self.url, {"sede": str(self.otra_sede.pk)}, **auth_prueba(self.admin)
        )

        self.assertEqual(len(todas.data["resultados"]), 1)
        self.assertEqual(de_otra.data["resultados"], [])

    def test_los_correos_al_cliente_no_aparecen_en_el_panel(self):
        with self.captureOnCommitCallbacks(execute=True):
            self._pedido()  # deja un registro de correo de confirmación

        respuesta = self.client.get(self.url, **auth_prueba(self.operador))

        self.assertEqual(respuesta.data["resultados"], [])

    def test_marcar_como_leida(self):
        self._cancelar(self._pedido())
        alerta = self._alertas().get()

        respuesta = self.client.patch(
            reverse("notificacion_detalle", args=[alerta.pk]),
            {"leida": True, "mensaje": "intento de cambio"},
            format="json",
            **auth_prueba(self.operador),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        alerta.refresh_from_db()
        self.assertTrue(alerta.leida)
        self.assertNotEqual(alerta.mensaje, "intento de cambio")
        no_leidas = self.client.get(self.url, {"leida": "false"}, **auth_prueba(self.operador))
        self.assertEqual(no_leidas.data["no_leidas"], 0)
        self.assertEqual(no_leidas.data["resultados"], [])

    def test_no_se_marca_la_alerta_de_otra_sede(self):
        self._cancelar(self._pedido())
        alerta = self._alertas().get()

        respuesta = self.client.patch(
            reverse("notificacion_detalle", args=[alerta.pk]),
            {"leida": True},
            format="json",
            **auth_prueba(self.operador_otra),
        )

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_marcar_todas_como_leidas(self):
        self._cancelar(self._pedido())
        self._cancelar(self._pedido())

        respuesta = self.client.post(
            reverse("notificacion_marcar_leidas"), **auth_prueba(self.operador)
        )

        self.assertEqual(respuesta.data["marcadas"], 2)
        self.assertFalse(self._alertas().filter(leida=False).exists())

    def test_solo_personal_de_panel(self):
        self.assertEqual(self.client.get(self.url, **auth_prueba(self.cliente)).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_el_cancelado_sale_de_entrantes_y_del_tablero(self):
        cancelado = self._pedido()
        activo = self._pedido()
        self._cancelar(cancelado)

        entrantes = self.client.get(
            reverse("pedido_list_create"), {"estado": "recibido"}, **auth_prueba(self.operador)
        )
        tablero = self.client.get(
            reverse("pedido_list_create"),
            {"estado": "recibido,en_preparacion,listo_despacho"},
            **auth_prueba(self.operador),
        )

        self.assertEqual([p["id"] for p in entrantes.data], [activo.pk])
        self.assertEqual([p["id"] for p in tablero.data], [activo.pk])
