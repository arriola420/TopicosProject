from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.domain.orden_builder import OrdenBuilder
from core.infra.notificador_factory import (
    NotificadorEmail,
    NotificadorFactory,
    NotificadorMock,
)
from core.models import (
    Categoria,
    Cliente,
    Cupon,
    Genero,
    Producto,
    TipoDescuento,
    Variante,
    Vendedor,
)
from core.services import OrdenService


class OrdenFixtureMixin:
    def setUp(self):
        self.cliente = Cliente.objects.create_user(
            username='cliente', email='cliente@example.com', password='secret123'
        )
        self.vendedor = Vendedor.objects.create_user(
            username='vendedor', email='vendedor@example.com', password='secret123',
            nombre_marca='Marca Demo', comision_pct=0.10,
        )
        categoria = Categoria.objects.create(nombre='Camisetas', genero=Genero.UNISEX)
        producto = Producto.objects.create(
            vendedor=self.vendedor, categoria=categoria, nombre='Camiseta', precio_base=100,
        )
        self.variante = Variante.objects.create(
            producto=producto, sku='CAM-001', talla='M', color='Negro', stock=5, precio=100,
        )

    def items(self, cantidad=2):
        return [{'variante': self.variante, 'cantidad': cantidad}]


class OrdenBuilderTests(OrdenFixtureMixin, TestCase):
    def test_construye_orden_valida_y_reduce_stock(self):
        orden = OrdenBuilder().para_cliente(self.cliente).con_items(self.items()).build()

        self.assertEqual(orden.total, 200)
        self.assertEqual(orden.subordenes.count(), 1)
        self.assertEqual(orden.subordenes.get().detalles.count(), 1)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 3)

    def test_rechaza_cantidad_no_positiva(self):
        with self.assertRaisesRegex(ValueError, 'Cantidad inválida'):
            OrdenBuilder().para_cliente(self.cliente).con_items(self.items(0)).build()

    def test_suma_items_repetidos_al_validar_stock(self):
        items = self.items(3) + self.items(3)
        with self.assertRaisesRegex(ValueError, 'Stock insuficiente'):
            OrdenBuilder().para_cliente(self.cliente).con_items(items).build()

    def test_no_consume_cupon_si_no_alcanza_compra_minima(self):
        cupon = Cupon.objects.create(
            codigo='MINIMO', tipo=TipoDescuento.MONTO_FIJO, valor=10,
            compra_minima=500, usos_disponibles=1,
            fecha_vencimiento=timezone.now().date() + timedelta(days=1),
        )
        with self.assertRaisesRegex(ValueError, 'monto mínimo'):
            (OrdenBuilder().para_cliente(self.cliente).con_items(self.items(1))
             .con_cupon(cupon).build())
        cupon.refresh_from_db()
        self.assertEqual(cupon.usos_disponibles, 1)


class NotificadorFactoryTests(TestCase):
    @patch.dict('os.environ', {'NOTIFICADOR_TYPE': 'MOCK'})
    def test_crea_mock_desde_variable_de_entorno(self):
        self.assertIsInstance(NotificadorFactory.crear(), NotificadorMock)

    @patch.dict('os.environ', {'NOTIFICADOR_TYPE': 'REAL'})
    def test_crea_email_desde_variable_de_entorno(self):
        self.assertIsInstance(NotificadorFactory.crear(), NotificadorEmail)


class OrdenServiceTests(OrdenFixtureMixin, TestCase):
    def test_usa_notificador_inyectado(self):
        notificador = Mock()
        orden = OrdenService(notificador=notificador).procesar_orden(
            self.cliente, self.items(1)
        )
        notificador.enviar_confirmacion.assert_called_once_with(orden)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProcesarOrdenViewTests(OrdenFixtureMixin, TestCase):
    def test_endpoint_procesa_orden(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse('core:procesar-orden'),
            {'variante_id': [self.variante.pk], 'cantidad': ['1']},
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['ok'])

    def test_api_json_rechaza_stock_con_conflicto(self):
        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse('core:ordenes'),
            {'items': [{'variante': self.variante.pk, 'cantidad': 6}]},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 409)

    def test_api_detalle_no_expone_orden_de_otro_cliente(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('core:orden-detalle', args=[99999]))

        self.assertEqual(response.status_code, 404)

    def test_pago_no_reduce_stock_por_segunda_vez(self):
        self.client.force_login(self.cliente)
        crear = self.client.post(
            reverse('core:ordenes'),
            {'items': [{'variante': self.variante.pk, 'cantidad': 1}]},
            content_type='application/json',
        )
        orden_id = crear.json()['orden_id']
        response = self.client.post(
            reverse('core:pagar-orden', args=[orden_id]),
            {'metodo': 'TARJETA'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 4)


class HomeViewTests(TestCase):
    def test_home_carga(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marketplace Core')
