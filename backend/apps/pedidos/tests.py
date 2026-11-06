from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.datos_prueba import negocio_de_rol, negocio_prueba
from apps.inventario.models import InventarioSede
from apps.menu.models import (
    GrupoOpcion,
    OpcionProducto,
    Producto,
    ProductoCombo,
)
from apps.notificaciones.models import Notificacion, TipoNotificacion
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import (
    DetallePedido,
    EstadoPedido,
    HistorialEstado,
    Pedido,
    TipoPedido,
)
from .services import cambiar_estado_pedido, crear_pedido

PASSWORD = "ClaveSegura#2024"


class PedidoInventarioTests(APITestCase):
    def setUp(self):
        self.operador = self._crear_usuario(
            Rol.OPERADOR, "operador.pedidos@example.com"
        )
        self.cliente = self._crear_usuario(
            Rol.CLIENTE, "cliente.pedidos@example.com"
        )
        self.operador_token = self._token(self.operador)
        self.cliente_token = self._token(self.cliente)

        self.sede = Sede.objects.create(
            negocio=negocio_prueba(),
            nombre="Sede Norte",
            direccion="Calle 20 # 30-40",
        )
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)

        self.producto = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Hamburguesa",
            precio_base=Decimal("15000.00"),
            tiempo_preparacion_min=15,
        )
        self.adicional = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Limonada",
            precio_base=Decimal("5000.00"),
            tiempo_preparacion_min=5,
        )
        self.combo = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Combo Hamburguesa",
            precio_base=Decimal("20000.00"),
            tiempo_preparacion_min=20,
            es_combo=True,
        )
        ProductoCombo.objects.create(
            combo=self.combo,
            producto=self.producto,
            cantidad=2,
        )
        ProductoCombo.objects.create(
            combo=self.combo,
            producto=self.adicional,
            cantidad=1,
        )

        self.inventario_producto = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.producto,
            stock_actual=10,
            stock_minimo=3,
        )
        self.inventario_adicional = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.adicional,
            stock_actual=10,
            stock_minimo=3,
        )
        self.inventario_combo = InventarioSede.objects.create(
            sede=self.sede,
            producto=self.combo,
            stock_actual=50,
            stock_minimo=3,
        )

        self.pedidos_url = reverse("pedido_list_create")

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol),
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Pedidos",
            telefono="3000000000",
            rol=rol,
        )

    def _token(self, usuario):
        return str(LoginSerializer.get_token(usuario).access_token)

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _payload(self, *, producto=None, cantidad=1, **overrides):
        data = {
            "sede_id": str(self.sede.pk),
            "cliente_nombre": "Ana Perez",
            "cliente_telefono": "3100000000",
            "metodo_pago": "efectivo",
            "detalles": [
                {
                    "producto_id": str((producto or self.producto).pk),
                    "cantidad": cantidad,
                }
            ],
        }
        data.update(overrides)
        return data

    def test_pedido_simple_descuenta_stock_de_la_sede(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(DetallePedido.objects.count(), 1)
        self.assertEqual(response.data["estado"], "recibido")
        self.assertEqual(len(response.data["detalles"]), 1)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 8)

    def test_pedido_con_combo_descuenta_todos_sus_componentes(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(producto=self.combo, cantidad=3),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.inventario_adicional.refresh_from_db()
        self.inventario_combo.refresh_from_db()

        self.assertEqual(self.inventario_producto.stock_actual, 4)
        self.assertEqual(self.inventario_adicional.stock_actual, 7)
        self.assertEqual(self.inventario_combo.stock_actual, 50)

    def test_stock_insuficiente_devuelve_400_y_revierte_todo(self):
        self.inventario_producto.stock_actual = 1
        self.inventario_producto.save(update_fields=["stock_actual"])

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Stock insuficiente para el producto", str(response.data))
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(DetallePedido.objects.count(), 0)
        self.assertEqual(Notificacion.objects.count(), 0)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 1)

    def test_descuento_hasta_el_minimo_genera_alerta_de_stock_bajo(self):
        self.inventario_producto.stock_actual = 10
        self.inventario_producto.stock_minimo = 5
        self.inventario_producto.save(
            update_fields=["stock_actual", "stock_minimo"]
        )

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=5),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 5)
        self.assertEqual(Notificacion.objects.count(), 1)
        self.assertEqual(
            Notificacion.objects.get().tipo,
            TipoNotificacion.ALERTA_STOCK_BAJO,
        )

    def test_producto_sin_control_de_stock_no_se_descuenta(self):
        self.inventario_producto.controla_stock = False
        self.inventario_producto.stock_actual = 1
        self.inventario_producto.save(
            update_fields=["controla_stock", "stock_actual"]
        )

        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=2),
            format="json",
            **self._auth(self.operador_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.inventario_producto.refresh_from_db()
        self.assertEqual(self.inventario_producto.stock_actual, 1)

    def test_cliente_autenticado_puede_crear_pedido(self):
        response = self.client.post(
            self.pedidos_url,
            self._payload(cantidad=1),
            format="json",
            **self._auth(self.cliente_token),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.creado_por, self.cliente)


class PedidoOperacionTests(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(negocio=negocio_prueba(), nombre="Sede Norte", direccion="Calle 1")
        self.otra_sede = Sede.objects.create(negocio=negocio_prueba(), nombre="Sede Sur", direccion="Calle 2")

        self.admin = self._crear_usuario(Rol.ADMIN, "admin@example.com")
        self.operador = self._crear_usuario(Rol.OPERADOR, "operador@example.com")
        self.cocina = self._crear_usuario(Rol.COCINA, "cocina@example.com")
        self.cliente = self._crear_usuario(Rol.CLIENTE, "cliente@example.com")
        self.repartidor = self._crear_usuario(Rol.REPARTIDOR, "repartidor@example.com")
        SedeUsuario.objects.create(usuario=self.operador, sede=self.sede)
        SedeUsuario.objects.create(usuario=self.cocina, sede=self.sede)

        self.producto = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Hamburguesa",
            precio_base=Decimal("15000.00"),
            tiempo_preparacion_min=15,
        )
        for sede in (self.sede, self.otra_sede):
            InventarioSede.objects.create(
                sede=sede, producto=self.producto, controla_stock=False
            )
        self.pedido = self._crear_pedido(self.sede)
        self.pedido_ajeno = self._crear_pedido(self.otra_sede)

        self.url = reverse("pedido_list_create")

    def _crear_usuario(self, rol, email):
        return User.objects.create_user(
            negocio=negocio_de_rol(rol),
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Pedidos",
            telefono="3000000000",
            rol=rol,
        )

    def _crear_pedido(self, sede, **extra):
        return crear_pedido(
            sede=sede,
            detalles=[{"producto": self.producto, "cantidad": 1}],
            cliente_nombre="Ana",
            **extra,
        )

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _cambiar_estado(self, pedido, estado, usuario=None):
        return self.client.patch(
            reverse("pedido_estado", args=[pedido.pk]),
            {"estado": estado},
            format="json",
            **self._auth(usuario or self.cocina),
        )

    def _ids(self, response):
        return {pedido["id"] for pedido in response.data}

    def test_personal_solo_ve_pedidos_de_sus_sedes(self):
        for usuario in (self.operador, self.cocina):
            with self.subTest(rol=usuario.rol):
                response = self.client.get(self.url, **self._auth(usuario))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(self._ids(response), {self.pedido.pk})

    def test_personal_no_filtra_por_sede_ajena(self):
        response = self.client.get(
            self.url, {"sede": str(self.otra_sede.pk)}, **self._auth(self.operador)
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_ve_todas_las_sedes_y_puede_filtrar(self):
        response = self.client.get(self.url, **self._auth(self.admin))
        self.assertEqual(
            self._ids(response), {self.pedido.pk, self.pedido_ajeno.pk}
        )

        response = self.client.get(
            self.url, {"sede": str(self.otra_sede.pk)}, **self._auth(self.admin)
        )
        self.assertEqual(self._ids(response), {self.pedido_ajeno.pk})

    def test_filtra_por_uno_o_varios_estados(self):
        en_preparacion = self._crear_pedido(self.sede)
        self._cambiar_estado(en_preparacion, "en_preparacion")

        response = self.client.get(
            self.url, {"estado": "en_preparacion"}, **self._auth(self.cocina)
        )
        self.assertEqual(self._ids(response), {en_preparacion.pk})

        response = self.client.get(
            self.url,
            {"estado": "recibido,en_preparacion"},
            **self._auth(self.cocina),
        )
        self.assertEqual(self._ids(response), {self.pedido.pk, en_preparacion.pk})

    def test_estado_invalido_en_filtro_da_400(self):
        response = self.client.get(
            self.url, {"estado": "inventado"}, **self._auth(self.cocina)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtra_por_fecha(self):
        hoy = timezone.localdate()
        ayer = hoy - timedelta(days=1)
        Pedido.objects.filter(pk=self.pedido_ajeno.pk).update(
            creado_en=timezone.now() - timedelta(days=1)
        )

        response = self.client.get(
            self.url, {"fecha": str(hoy)}, **self._auth(self.admin)
        )
        self.assertEqual(self._ids(response), {self.pedido.pk})

        response = self.client.get(
            self.url, {"fecha": str(ayer)}, **self._auth(self.admin)
        )
        self.assertEqual(self._ids(response), {self.pedido_ajeno.pk})

    def test_cliente_solo_lista_sus_pedidos(self):
        propio = self._crear_pedido(self.sede, cliente=self.cliente)

        response = self.client.get(self.url, **self._auth(self.cliente))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {propio.pk})
        self.assertEqual(response.data[0]["sede_nombre"], "Sede Norte")
        self.assertEqual(response.data[0]["negocio_nombre"], self.sede.negocio.nombre)

    def test_cliente_filtra_sus_pedidos_por_sede_sin_trabajar_en_ella(self):
        self._crear_pedido(self.sede, cliente=self.cliente)
        en_otra = self._crear_pedido(self.otra_sede, cliente=self.cliente)

        response = self.client.get(
            self.url, {"sede": str(self.otra_sede.pk)}, **self._auth(self.cliente)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {en_otra.pk})

    def test_cliente_no_avanza_el_estado_de_su_propio_pedido(self):
        propio = self._crear_pedido(self.sede, cliente=self.cliente)

        response = self._cambiar_estado(propio, "en_preparacion", self.cliente)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_listar_pedidos_exige_sesion(self):
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_flujo_recoger_termina_en_entregado(self):
        for estado in ("en_preparacion", "listo_despacho", "entregado"):
            response = self._cambiar_estado(self.pedido, estado)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["estado"], estado)

        self.assertEqual(response.data["estados_siguientes"], [])
        historial = HistorialEstado.objects.filter(pedido=self.pedido)
        self.assertEqual(historial.count(), 4)
        self.assertEqual(
            historial.filter(cambiado_por=self.cocina).count(), 3
        )

    def test_flujo_domicilio_pasa_por_en_camino(self):
        pedido = self._crear_pedido(
            self.sede,
            tipo="domicilio",
            direccion_entrega="Calle 5",
            entrega_lat=Decimal("3.45"),
            entrega_lng=Decimal("-76.53"),
        )
        self._cambiar_estado(pedido, "en_preparacion")
        self._cambiar_estado(pedido, "listo_despacho")

        response = self._cambiar_estado(pedido, "entregado")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self._cambiar_estado(pedido, "en_camino")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estados_siguientes"], ["entregado"])

        response = self._cambiar_estado(pedido, "entregado", self.operador)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pedido_para_recoger_no_pasa_a_en_camino(self):
        self._cambiar_estado(self.pedido, "en_preparacion")
        self._cambiar_estado(self.pedido, "listo_despacho")

        response = self._cambiar_estado(self.pedido, "en_camino")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transicion_invalida_no_cambia_nada(self):
        response = self._cambiar_estado(self.pedido, "entregado")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, "recibido")
        self.assertEqual(
            HistorialEstado.objects.filter(pedido=self.pedido).count(), 1
        )

    def test_personal_de_otra_sede_no_cambia_estado(self):
        for usuario in (self.operador, self.cocina):
            with self.subTest(rol=usuario.rol):
                response = self._cambiar_estado(
                    self.pedido_ajeno, "en_preparacion", usuario
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.pedido_ajeno.refresh_from_db()
        self.assertEqual(self.pedido_ajeno.estado, "recibido")

    def test_admin_cambia_estado_de_cualquier_sede(self):
        response = self._cambiar_estado(
            self.pedido_ajeno, "en_preparacion", self.admin
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cliente_no_cambia_estado_y_pedido_inexistente_da_404(self):
        response = self._cambiar_estado(self.pedido, "en_preparacion", self.cliente)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(
            reverse("pedido_estado", args=[999999]),
            {"estado": "en_preparacion"},
            format="json",
            **self._auth(self.cocina),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def _payload(self, **extra):
        return {
            "sede_id": str(self.sede.pk),
            "detalles": [{"producto_id": str(self.producto.pk), "cantidad": 1}],
            **extra,
        }

    def test_operador_crea_pedido_a_nombre_de_cliente(self):
        response = self.client.post(
            self.url,
            self._payload(cliente_id=str(self.cliente.pk), canal="telefono"),
            format="json",
            **self._auth(self.operador),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = Pedido.objects.get(pk=response.data["id"])
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.creado_por, self.operador)
        self.assertEqual(pedido.cliente_nombre, self.cliente.nombre_completo)

    def test_cliente_id_debe_ser_un_cliente_activo(self):
        inactivo = self._crear_usuario(Rol.CLIENTE, "inactivo@example.com")
        inactivo.is_active = False
        inactivo.save(update_fields=["is_active"])

        for usuario in (self.cocina, inactivo):
            with self.subTest(usuario=usuario.email):
                response = self.client.post(
                    self.url,
                    self._payload(cliente_id=str(usuario.pk)),
                    format="json",
                    **self._auth(self.operador),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_operador_no_crea_pedido_en_sede_ajena(self):
        response = self.client.post(
            self.url,
            self._payload(sede_id=str(self.otra_sede.pk)),
            format="json",
            **self._auth(self.operador),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cliente_no_compra_a_nombre_de_otro_ni_fija_descuento(self):
        otro = self._crear_usuario(Rol.CLIENTE, "otro@example.com")

        response = self.client.post(
            self.url,
            self._payload(cliente_id=str(otro.pk), descuento="15000.00"),
            format="json",
            **self._auth(self.cliente),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pedido = Pedido.objects.get(pk=response.data["id"])
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.descuento, Decimal("0.00"))
        self.assertEqual(pedido.total, Decimal("15000.00"))

    def test_el_producto_debe_venderse_en_la_sede(self):
        sin_fila = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Sin fila",
            precio_base=Decimal("1000.00"),
            tiempo_preparacion_min=5,
        )
        no_disponible = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Apagado",
            precio_base=Decimal("1000.00"),
            tiempo_preparacion_min=5,
        )
        InventarioSede.objects.create(
            sede=self.sede, producto=no_disponible, disponible_en_sede=False
        )
        pedidos_antes = Pedido.objects.count()

        for producto in (sin_fila, no_disponible):
            with self.subTest(producto=producto.nombre):
                response = self.client.post(
                    self.url,
                    self._payload(
                        detalles=[
                            {"producto_id": str(producto.pk), "cantidad": 1}
                        ]
                    ),
                    format="json",
                    **self._auth(self.cliente),
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

        self.assertEqual(Pedido.objects.count(), pedidos_antes)

    def test_cantidad_maxima_por_linea_es_10(self):
        for cantidad, esperado in (
            (10, status.HTTP_201_CREATED),
            (11, status.HTTP_400_BAD_REQUEST),
        ):
            with self.subTest(cantidad=cantidad):
                response = self.client.post(
                    self.url,
                    self._payload(
                        detalles=[
                            {
                                "producto_id": str(self.producto.pk),
                                "cantidad": cantidad,
                            }
                        ]
                    ),
                    format="json",
                    **self._auth(self.cliente),
                )
                self.assertEqual(response.status_code, esperado)

    def test_stock_se_descuenta_al_crear_y_no_al_cambiar_estado(self):
        inventario = InventarioSede.objects.get(
            sede=self.sede, producto=self.producto
        )
        inventario.controla_stock = True
        inventario.stock_actual = 10
        inventario.save(update_fields=["controla_stock", "stock_actual"])

        response = self.client.post(
            self.url,
            self._payload(
                detalles=[
                    {"producto_id": str(self.producto.pk), "cantidad": 3}
                ]
            ),
            format="json",
            **self._auth(self.cliente),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inventario.refresh_from_db()
        self.assertEqual(inventario.stock_actual, 7)

        pedido = Pedido.objects.get(pk=response.data["id"])
        for estado in ("en_preparacion", "listo_despacho", "entregado"):
            self.assertEqual(
                self._cambiar_estado(pedido, estado).status_code,
                status.HTTP_200_OK,
            )

        inventario.refresh_from_db()
        self.assertEqual(inventario.stock_actual, 7)

    def test_pedido_con_opciones_suma_su_precio(self):
        grupo = GrupoOpcion.objects.create(
            producto=self.producto, nombre="Tamaños", tipo="tamano"
        )
        opcion = OpcionProducto.objects.create(
            grupo=grupo, nombre="Grande", precio_adicional=Decimal("3000.00")
        )

        response = self.client.post(
            self.url,
            self._payload(
                detalles=[
                    {
                        "producto_id": str(self.producto.pk),
                        "cantidad": 2,
                        "notas_producto": "Sin sal",
                        "opciones": [str(opcion.pk)],
                    }
                ]
            ),
            format="json",
            **self._auth(self.cliente),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total"], "36000.00")
        detalle = response.data["detalles"][0]
        self.assertEqual(detalle["notas_producto"], "Sin sal")
        self.assertEqual(detalle["opciones"][0]["nombre_opcion"], "Grande")

    def test_ingrediente_excluible_se_guarda_como_sin(self):
        grupo = GrupoOpcion.objects.create(
            producto=self.producto, nombre="Quitar", tipo="excluible"
        )
        cebolla = OpcionProducto.objects.create(grupo=grupo, nombre="Cebolla")
        ya_con_sin = OpcionProducto.objects.create(grupo=grupo, nombre="Sin sal")

        response = self.client.post(
            self.url,
            self._payload(
                detalles=[
                    {
                        "producto_id": str(self.producto.pk),
                        "cantidad": 1,
                        "opciones": [str(cebolla.pk), str(ya_con_sin.pk)],
                    }
                ]
            ),
            format="json",
            **self._auth(self.cliente),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        nombres = {
            opcion["nombre_opcion"]
            for opcion in response.data["detalles"][0]["opciones"]
        }
        self.assertEqual(nombres, {"Sin cebolla", "Sin sal"})


class PedidoRepartidorTests(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Sede Norte", direccion="Calle 1"
        )
        self.otra_sede = Sede.objects.create(
            negocio=negocio_prueba(), nombre="Sede Sur", direccion="Calle 2"
        )
        self.repartidor = self._crear_repartidor("repartidor@example.com")
        self.colega = self._crear_repartidor("colega@example.com")
        self.producto = Producto.objects.create(
            negocio=negocio_prueba(),
            nombre="Hamburguesa",
            precio_base=Decimal("15000.00"),
            tiempo_preparacion_min=15,
        )
        for sede in (self.sede, self.otra_sede):
            InventarioSede.objects.create(
                sede=sede, producto=self.producto, controla_stock=False
            )
        self.url = reverse("pedido_list_create")

    def _crear_repartidor(self, email):
        usuario = User.objects.create_user(
            negocio=negocio_de_rol(Rol.REPARTIDOR),
            email=email,
            password=PASSWORD,
            nombre="Prueba",
            apellido="Reparto",
            telefono="3000000000",
            rol=Rol.REPARTIDOR,
        )
        SedeUsuario.objects.create(usuario=usuario, sede=self.sede)
        return usuario

    def _pedido(self, estado=EstadoPedido.LISTO_DESPACHO, sede=None, tipo=TipoPedido.DOMICILIO):
        pedido = crear_pedido(
            sede=sede or self.sede,
            detalles=[{"producto": self.producto, "cantidad": 1}],
            cliente_nombre="Ana",
            tipo=tipo,
            direccion_entrega="Carrera 5",
            entrega_lat=Decimal("3.45"),
            entrega_lng=Decimal("-76.53"),
        )
        Pedido.objects.filter(pk=pedido.pk).update(estado=estado)
        pedido.refresh_from_db()
        return pedido

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _cambiar_estado(self, pedido, estado, usuario=None):
        return self.client.patch(
            reverse("pedido_estado", args=[pedido.pk]),
            {"estado": estado},
            format="json",
            **self._auth(usuario or self.repartidor),
        )

    def _ids(self, usuario=None):
        response = self.client.get(self.url, **self._auth(usuario or self.repartidor))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {pedido["id"] for pedido in response.data}

    def test_solo_ve_domicilios_despachables_de_sus_sedes(self):
        listo = self._pedido()
        en_camino_sin_asignar = self._pedido(EstadoPedido.EN_CAMINO)
        self._pedido(EstadoPedido.EN_PREPARACION)
        self._pedido(tipo=TipoPedido.RECOGER)
        self._pedido(sede=self.otra_sede)

        self.assertEqual(self._ids(), {listo.pk, en_camino_sin_asignar.pk})

    def test_flujo_de_entrega_asigna_el_pedido_y_termina_en_entregado(self):
        pedido = self._pedido()

        response = self._cambiar_estado(pedido, "en_camino")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estados_siguientes"], ["entregado"])
        pedido.refresh_from_db()
        self.assertEqual(pedido.repartidor, self.repartidor)

        response = self._cambiar_estado(pedido, "entregado")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.ENTREGADO)
        self.assertEqual(
            pedido.historial.filter(cambiado_por=self.repartidor).count(), 2
        )

    def test_no_salta_de_listo_a_entregado(self):
        pedido = self._pedido()

        response = self._cambiar_estado(pedido, "entregado")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.LISTO_DESPACHO)
        self.assertIsNone(pedido.repartidor)

    def test_pedido_tomado_desaparece_para_otro_repartidor(self):
        pedido = self._pedido()
        self._cambiar_estado(pedido, "en_camino")

        self.assertEqual(self._ids(self.colega), set())
        self.assertEqual(self._ids(), {pedido.pk})
        response = self._cambiar_estado(pedido, "entregado", self.colega)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.EN_CAMINO)
        self.assertEqual(pedido.repartidor, self.repartidor)

    def test_servicio_rechaza_pedido_tomado_por_otro_durante_la_carrera(self):
        pedido = self._pedido()
        cambiar_estado_pedido(pedido.pk, estado="en_camino", usuario=self.repartidor)

        with self.assertRaisesMessage(ValueError, "ya lo tomó otro repartidor"):
            cambiar_estado_pedido(pedido.pk, estado="entregado", usuario=self.colega)

    def test_no_toca_pedidos_fuera_de_su_alcance(self):
        casos = (
            self._pedido(EstadoPedido.RECIBIDO),
            self._pedido(EstadoPedido.EN_PREPARACION),
            self._pedido(tipo=TipoPedido.RECOGER),
            self._pedido(sede=self.otra_sede),
        )
        for pedido in casos:
            for estado in ("en_preparacion", "listo_despacho", "en_camino", "entregado"):
                with self.subTest(pedido=pedido.pk, estado=estado):
                    response = self._cambiar_estado(pedido, estado)
                    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_sin_sede_asignada_no_ve_pedidos(self):
        self._pedido()
        SedeUsuario.objects.filter(usuario=self.repartidor).delete()

        self.assertEqual(self._ids(), set())

    def test_repartidor_no_crea_pedidos(self):
        response = self.client.post(
            self.url,
            {
                "sede_id": str(self.sede.pk),
                "detalles": [{"producto_id": str(self.producto.pk), "cantidad": 1}],
            },
            format="json",
            **self._auth(self.repartidor),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
