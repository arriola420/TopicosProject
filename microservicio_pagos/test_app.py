import unittest

from app import app


class PagosAPITests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_procesa_pago_valido(self):
        response = self.client.post(
            '/api/v2/pagos/procesar',
            json={'orden_id': 15, 'monto': 120000, 'metodo': 'PSE'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['estado'], 'PROCESADO')
        self.assertEqual(response.get_json()['servicio'], 'Microservicio Flask de Pagos (v2)')

    def test_rechaza_json_incompleto(self):
        response = self.client.post('/api/v2/pagos/procesar', json={'orden_id': 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn('campos', response.get_json())


if __name__ == '__main__':
    unittest.main()
