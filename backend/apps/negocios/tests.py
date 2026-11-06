"""Aislamiento entre negocios: nadie ve ni modifica datos de otro."""

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventario.models import InventarioSede
from apps.menu.models import Categoria, Producto
from apps.pedidos.models import Pedido
from apps.pedidos.services import crear_pedido
from apps.promociones.models import Promocion
from apps.sedes.models import Sede, SedeUsuario
from apps.usuarios.models import Rol, User
from apps.usuarios.serializers import LoginSerializer

from .models import Negocio

CLAVE = "ClaveSegura#2024"


class DatosDosNegocios(APITestCase):
    def setUp(self):
        self.a = self._negocio("A")
        self.b = self._negocio("B")
        self.cliente = User.objects.create_user(
            email="cliente@example.com", password=CLAVE, nombre="Ana",
            apellido="Cliente", telefono="3100000000",
        )

    def _negocio(self, letra):
        negocio = Negocio.objects.create(nombre=f"Negocio {letra}")
        admin = self._usuario(f"admin{letra}@example.com", Rol.ADMIN, negocio)
        operador = self._usuario(f"operador{letra}@example.com", Rol.OPERADOR, negocio)
        cocina = self._usuario(f"cocina{letra}@example.com", Rol.COCINA, negocio)
        sede = Sede.objects.create(negocio=negocio, nombre=f"Sede {letra}", direccion="Calle 1")
        SedeUsuario.objects.create(usuario=operador, sede=sede)
        SedeUsuario.objects.create(usuario=cocina, sede=sede)
        categoria = Categoria.objects.create(negocio=negocio, nombre=f"Categoria {letra}")
        producto = Producto.objects.create(
            negocio=negocio, categoria=categoria, nombre=f"Producto {letra}",
            precio_base=Decimal("10000"), tiempo_preparacion_min=5,
        )
        inventario = InventarioSede.objects.create(
            sede=sede, producto=producto, stock_actual=10
        )
        hoy = timezone.localdate()
        promocion = Promocion.objects.create(
            negocio=negocio, nombre=f"Promo {letra}", porcentaje_descuento=Decimal("10"),
            cupo_maximo_diario=5, fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=1),
        )
        pedido = crear_pedido(
            sede=sede, cliente_nombre=f"Cliente {letra}",
            detalles=[{"producto": producto, "cantidad": 1}],
        )
        return Datos(
            negocio=negocio, admin=admin, operador=operador, cocina=cocina, sede=sede,
            categoria=categoria, producto=producto, inventario=inventario,
            promocion=promocion, pedido=pedido,
        )

    def _usuario(self, email, rol, negocio):
        return User.objects.create_user(
            email=email, password=CLAVE, nombre="Prueba", apellido=rol,
            telefono="3000000000", rol=rol, negocio=negocio,
        )

    def _auth(self, usuario):
        token = LoginSerializer.get_token(usuario).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class Datos:
    def __init__(self, **campos):
        self.__dict__.update(campos)


class RegistroNegocioTests(APITestCase):
    def setUp(self):
        self.url = reverse("registro_negocio")

    def _payload(self, **extra):
        return {
            "negocio_nombre": "La Parrilla",
            "negocio_descripcion": "Carnes",
            "nombre": "Dora",
            "apellido": "Duena",
            "email": "Dora@Example.com",
            "telefono": "3001112233",
            "password": CLAVE,
            "password_confirmacion": CLAVE,
            **extra,
        }

    def test_crea_negocio_y_admin_responsable(self):
        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("access", response.data)
        usuario = User.objects.get(email="dora@example.com")
        self.assertEqual(usuario.rol, Rol.ADMIN)
        self.assertEqual(usuario.negocio.nombre, "La Parrilla")
        self.assertEqual(usuario.negocio.descripcion, "Carnes")
        self.assertEqual(str(usuario.negocio_id), response.data["negocio"]["id"])

    def test_login_devuelve_el_negocio(self):
        self.client.post(self.url, self._payload(), format="json")

        response = self.client.post(
            reverse("login"),
            {"email": "dora@example.com", "password": CLAVE},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["negocio"]["nombre"], "La Parrilla")

    def test_el_cuerpo_no_puede_elegir_otro_negocio_ni_rol(self):
        ajeno = Negocio.objects.create(nombre="Ajeno")

        self.client.post(
            self.url,
            self._payload(negocio=str(ajeno.pk), negocio_id=str(ajeno.pk), rol=Rol.CLIENTE),
            format="json",
        )

        usuario = User.objects.get(email="dora@example.com")
        self.assertNotEqual(usuario.negocio_id, ajeno.pk)
        self.assertEqual(usuario.rol, Rol.ADMIN)
        self.assertFalse(usuario.is_superuser)

    def test_datos_invalidos_no_crean_negocio(self):
        User.objects.create_user(
            email="dora@example.com", password=CLAVE, nombre="Otra",
            apellido="Persona", telefono="3000000000",
        )
        casos = (
            ({}, "email"),  # correo repetido
            ({"email": "n@example.com", "password": "12345678", "password_confirmacion": "12345678"}, "password"),
            ({"email": "n@example.com", "negocio_nombre": "  "}, "negocio_nombre"),
        )

        for cambios, campo in casos:
            with self.subTest(campo=campo):
                response = self.client.post(
                    self.url, self._payload(**cambios), format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, response.data)

        self.assertFalse(Negocio.objects.exists())

    def test_correo_repetido_tiene_mensaje_claro(self):
        self.client.post(self.url, self._payload(), format="json")

        response = self.client.post(
            self.url, self._payload(email="DORA@example.com"), format="json"
        )

        self.assertEqual(
            response.data["email"],
            ["Ya existe un usuario registrado con este correo."],
        )


class AislamientoLecturaTests(DatosDosNegocios):
    def _ids(self, url, usuario, **parametros):
        response = self.client.get(url, parametros, **self._auth(usuario))
        self.assertEqual(response.status_code, status.HTTP_200_OK, url)
        return {str(item["id"]) for item in response.data}

    def test_sedes(self):
        self.assertEqual(
            self._ids(reverse("sede_list_create"), self.a.admin, incluir_inactivas="true"),
            {str(self.a.sede.pk)},
        )
        self.assertEqual(
            self._ids(reverse("sede_list_create"), self.a.operador),
            {str(self.a.sede.pk)},
        )

    def test_el_publico_ve_las_sedes_de_todos_los_negocios(self):
        response = self.client.get(reverse("sede_list_create"))

        self.assertEqual(
            {s["negocio_nombre"] for s in response.data}, {"Negocio A", "Negocio B"}
        )

    def test_negocio_inactivo_desaparece_del_publico(self):
        self.b.negocio.activo = False
        self.b.negocio.save(update_fields=["activo"])

        sedes = self.client.get(reverse("sede_list_create")).data
        catalogo = self.client.get(reverse("catalogo_sede", args=[self.b.sede.pk]))

        self.assertEqual({s["negocio_nombre"] for s in sedes}, {"Negocio A"})
        self.assertEqual(catalogo.status_code, status.HTTP_404_NOT_FOUND)

    def test_categorias_y_productos(self):
        self.assertEqual(
            self._ids(reverse("categoria_list_create"), self.a.admin),
            {str(self.a.categoria.pk)},
        )
        self.assertEqual(
            self._ids(reverse("producto_list_create"), self.a.admin, incluir_inactivos="true"),
            {str(self.a.producto.pk)},
        )

    def test_el_personal_no_ve_otro_negocio_aunque_lo_pida(self):
        self.assertEqual(
            self._ids(reverse("producto_list_create"), self.a.admin, negocio=str(self.b.negocio.pk)),
            {str(self.a.producto.pk)},
        )

    def test_el_publico_filtra_el_menu_por_negocio(self):
        response = self.client.get(
            reverse("categoria_list_create"), {"negocio": str(self.b.negocio.pk)}
        )
        self.assertEqual({c["id"] for c in response.data}, {str(self.b.categoria.pk)})

        response = self.client.get(reverse("categoria_list_create"), {"negocio": "no-es-uuid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_producto_oculto_de_otro_negocio_no_se_ve(self):
        self.b.producto.disponible = False
        self.b.producto.save(update_fields=["disponible"])
        url = reverse("producto_detail", args=[self.b.producto.pk])

        self.assertEqual(
            self.client.get(url, **self._auth(self.a.admin)).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(url, **self._auth(self.b.admin)).status_code,
            status.HTTP_200_OK,
        )

    def test_inventario(self):
        for usuario in (self.a.admin, self.a.operador):
            response = self.client.get(
                reverse("inventario_sede", args=[self.b.sede.pk]), **self._auth(usuario)
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_promociones(self):
        self.assertEqual(
            self._ids(reverse("promocion_list_create"), self.a.admin, incluir_inactivas="true"),
            {str(self.a.promocion.pk)},
        )
        self.b.promocion.activa = False
        self.b.promocion.save(update_fields=["activa"])
        response = self.client.get(
            reverse("promocion_detail", args=[self.b.promocion.pk]),
            **self._auth(self.a.admin),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pedidos(self):
        for usuario in (self.a.admin, self.a.operador, self.a.cocina):
            response = self.client.get(reverse("pedido_list_create"), **self._auth(usuario))
            self.assertEqual({p["id"] for p in response.data}, {self.a.pedido.pk})

        response = self.client.get(
            reverse("pedido_list_create"),
            {"sede": str(self.b.sede.pk)},
            **self._auth(self.a.admin),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_personal(self):
        response = self.client.get(reverse("listar-usuarios"), **self._auth(self.a.admin))

        self.assertEqual(
            {u["email"] for u in response.data},
            {"adminA@example.com".lower(), "operadorA@example.com".lower(), "cocinaA@example.com".lower()},
        )

    def test_clientes_de_otro_negocio_no_se_listan(self):
        crear_pedido(
            sede=self.b.sede, cliente=self.cliente,
            detalles=[{"producto": self.b.producto, "cantidad": 1}],
        )
        url = reverse("clientes_busqueda")

        self.assertEqual(self.client.get(url, **self._auth(self.a.operador)).data, [])
        self.assertEqual(
            len(self.client.get(url, **self._auth(self.b.operador)).data), 1
        )

    def test_personal_sin_negocio_no_ve_nada(self):
        huerfano = self._usuario("huerfano@example.com", Rol.ADMIN, None)

        self.assertEqual(self._ids(reverse("sede_list_create"), huerfano), set())
        self.assertEqual(self._ids(reverse("producto_list_create"), huerfano), set())
        self.assertEqual(self._ids(reverse("pedido_list_create"), huerfano), set())
        self.assertEqual(
            self.client.get(reverse("listar-usuarios"), **self._auth(huerfano)).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(
                reverse("categoria_list_create"), {"nombre": "X"}, format="json",
                **self._auth(huerfano),
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )


class AislamientoEscrituraTests(DatosDosNegocios):
    def _pedir(self, metodo, url, datos=None, usuario=None):
        return getattr(self.client, metodo)(
            url, datos or {}, format="json", **self._auth(usuario or self.a.admin)
        )

    def test_no_modifica_recursos_de_otro_negocio(self):
        casos = [
            ("patch", reverse("sede_detail", args=[self.b.sede.pk]), {"nombre": "X"}),
            ("delete", reverse("sede_detail", args=[self.b.sede.pk]), None),
            ("post", reverse("sede_reactivar", args=[self.b.sede.pk]), None),
            ("patch", reverse("categoria_detail", args=[self.b.categoria.pk]), {"nombre": "X"}),
            ("delete", reverse("categoria_detail", args=[self.b.categoria.pk]), None),
            ("patch", reverse("producto_detail", args=[self.b.producto.pk]), {"nombre": "X"}),
            ("delete", reverse("producto_detail", args=[self.b.producto.pk]), None),
            (
                "post",
                reverse("producto_opciones", args=[self.b.producto.pk]),
                {"nombre": "Tamaños", "tipo": "tamano", "opciones": []},
            ),
            ("patch", reverse("promocion_detail", args=[self.b.promocion.pk]), {"nombre": "X"}),
            ("delete", reverse("promocion_detail", args=[self.b.promocion.pk]), None),
            ("patch", reverse("cambiar-rol", args=[self.b.operador.pk]), {"rol": "admin"}),
            ("patch", reverse("desactivar-usuario", args=[self.b.operador.pk]), None),
        ]

        for metodo, url, datos in casos:
            with self.subTest(metodo=metodo, url=url):
                self.assertEqual(
                    self._pedir(metodo, url, datos).status_code,
                    status.HTTP_404_NOT_FOUND,
                )

        self.b.sede.refresh_from_db()
        self.b.categoria.refresh_from_db()
        self.b.producto.refresh_from_db()
        self.b.promocion.refresh_from_db()
        self.b.operador.refresh_from_db()
        self.assertEqual(self.b.sede.nombre, "Sede B")
        self.assertTrue(self.b.sede.activa)
        self.assertEqual(self.b.categoria.nombre, "Categoria B")
        self.assertTrue(self.b.categoria.activa)
        self.assertEqual(self.b.producto.nombre, "Producto B")
        self.assertTrue(self.b.producto.disponible)
        self.assertFalse(self.b.producto.grupos_opcion.exists())
        self.assertEqual(self.b.promocion.nombre, "Promo B")
        self.assertTrue(self.b.promocion.activa)
        self.assertEqual(self.b.operador.rol, Rol.OPERADOR)
        self.assertTrue(self.b.operador.is_active)

    def test_lo_creado_queda_en_el_negocio_de_quien_lo_crea(self):
        sede = self._pedir("post", reverse("sede_list_create"), {"nombre": "Nueva", "direccion": "Calle 9"})
        categoria = self._pedir("post", reverse("categoria_list_create"), {"nombre": "Nueva"})
        producto = self._pedir(
            "post", reverse("producto_list_create"),
            {"nombre": "Nuevo", "precio_base": "100", "tiempo_preparacion_min": 5},
        )

        self.assertEqual(Sede.objects.get(pk=sede.data["id"]).negocio, self.a.negocio)
        self.assertEqual(Categoria.objects.get(pk=categoria.data["id"]).negocio, self.a.negocio)
        self.assertEqual(Producto.objects.get(pk=producto.data["id"]).negocio, self.a.negocio)

    def test_no_enlaza_recursos_de_otro_negocio(self):
        hoy = str(timezone.localdate())
        casos = [
            (
                "producto con categoria ajena", "post", reverse("producto_list_create"),
                {
                    "nombre": "X", "precio_base": "100", "tiempo_preparacion_min": 5,
                    "categoria_id": str(self.b.categoria.pk),
                },
            ),
            (
                "editar con categoria ajena", "patch",
                reverse("producto_detail", args=[self.a.producto.pk]),
                {"categoria_id": str(self.b.categoria.pk)},
            ),
            (
                "combo con producto ajeno", "post", reverse("combo_list_create"),
                {
                    "nombre": "X", "precio_base": "100",
                    "items_combo": [{"producto_id": str(self.b.producto.pk), "cantidad": 1}],
                },
            ),
            (
                "inventario con producto ajeno", "post",
                reverse("inventario_sede", args=[self.a.sede.pk]),
                {"producto_id": str(self.b.producto.pk), "stock_actual": 1},
            ),
            (
                "promocion con producto ajeno", "post", reverse("promocion_list_create"),
                {
                    "nombre": "X", "porcentaje_descuento": "10", "cupo_maximo_diario": 1,
                    "fecha_inicio": hoy, "fecha_fin": hoy,
                    "productos_ids": [str(self.b.producto.pk)],
                },
            ),
        ]

        for nombre, metodo, url, datos in casos:
            with self.subTest(caso=nombre):
                self.assertEqual(
                    self._pedir(metodo, url, datos).status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_promocion_no_se_asigna_a_sede_ajena(self):
        hoy = str(timezone.localdate())
        response = self._pedir(
            "post", reverse("promocion_list_create"),
            {
                "nombre": "X", "porcentaje_descuento": "10", "cupo_maximo_diario": 1,
                "fecha_inicio": hoy, "fecha_fin": hoy, "sede_id": str(self.b.sede.pk),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_el_mismo_codigo_de_promocion_sirve_en_dos_negocios(self):
        hoy = str(timezone.localdate())
        datos = {
            "nombre": "X", "codigo": "HOY10", "porcentaje_descuento": "10",
            "cupo_maximo_diario": 1, "fecha_inicio": hoy, "fecha_fin": hoy,
        }

        self.assertEqual(
            self._pedir("post", reverse("promocion_list_create"), datos).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self._pedir(
                "post", reverse("promocion_list_create"), datos, self.b.admin
            ).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self._pedir("post", reverse("promocion_list_create"), datos).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_personal_nuevo_queda_en_el_negocio_y_solo_usa_sus_sedes(self):
        datos = {
            "email": "nuevo@example.com", "nombre": "Nuevo", "apellido": "Empleado",
            "telefono": "3000000000", "rol": Rol.COCINA, "password": CLAVE,
            "password_confirmacion": CLAVE, "sedes_ids": [str(self.b.sede.pk)],
        }

        response = self._pedir("post", reverse("registro_personal"), datos)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="nuevo@example.com").exists())

        datos["sedes_ids"] = [str(self.a.sede.pk)]
        response = self._pedir("post", reverse("registro_personal"), datos)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            User.objects.get(email="nuevo@example.com").negocio, self.a.negocio
        )

    def test_admin_de_negocio_no_actua_sobre_pedidos_ajenos(self):
        for usuario in (self.a.admin, self.a.operador, self.a.cocina):
            response = self._pedir(
                "patch", reverse("pedido_estado", args=[self.b.pedido.pk]),
                {"estado": "en_preparacion"}, usuario,
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self._pedir(
            "post", reverse("pedido_list_create"),
            {
                "sede_id": str(self.b.sede.pk),
                "detalles": [{"producto_id": str(self.b.producto.pk), "cantidad": 1}],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.b.pedido.refresh_from_db()
        self.assertEqual(self.b.pedido.estado, "recibido")

    def test_cliente_no_mezcla_productos_de_otro_negocio(self):
        response = self._pedir(
            "post", reverse("pedido_list_create"),
            {
                "sede_id": str(self.a.sede.pk),
                "detalles": [{"producto_id": str(self.b.producto.pk), "cantidad": 1}],
            },
            self.cliente,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pedido.objects.count(), 2)

    def test_cliente_compra_en_cualquier_negocio(self):
        for datos in (self.a, self.b):
            response = self._pedir(
                "post", reverse("pedido_list_create"),
                {
                    "sede_id": str(datos.sede.pk),
                    "detalles": [{"producto_id": str(datos.producto.pk), "cantidad": 1}],
                },
                self.cliente,
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
