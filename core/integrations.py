from dataclasses import dataclass

import requests
from django.conf import settings


class IntegracionNoDisponible(Exception):
    """La integración remota no respondió con un contrato utilizable."""


@dataclass(frozen=True)
class ProductoExterno:
    nombre: str
    categoria: str
    precio: float
    imagen: str
    moneda: str = 'USD'


class ServicioAliadoAdapter:
    """Adapta el JSON del equipo aliado a un contrato estable del marketplace."""

    def __init__(self, base_url=None, timeout=4):
        self.base_url = (base_url or settings.ALLY_SERVICE_URL).rstrip('/')
        self.timeout = timeout

    def obtener_informacion(self):
        if not self.base_url:
            raise IntegracionNoDisponible(
                'Falta configurar ALLY_SERVICE_URL con el endpoint del equipo aliado.'
            )
        try:
            response = requests.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise IntegracionNoDisponible('El servicio aliado no está disponible.') from exc
        return {
            'fuente': 'equipo_aliado',
            'datos': payload,
        }


class CatalogoExternoAdapter:
    """Convierte el contrato de DummyJSON en recomendaciones propias."""

    def __init__(self, base_url=None, timeout=4):
        self.base_url = base_url or settings.THIRD_PARTY_PRODUCTS_URL
        self.timeout = timeout

    def obtener_recomendaciones(self, limite=6):
        try:
            response = requests.get(
                self.base_url,
                params={'limit': limite, 'select': 'title,price,thumbnail,category'},
                timeout=self.timeout,
            )
            response.raise_for_status()
            productos = response.json().get('products', [])
        except (requests.RequestException, ValueError, AttributeError) as exc:
            raise IntegracionNoDisponible('El catálogo externo no está disponible.') from exc

        return [
            ProductoExterno(
                nombre=item.get('title', 'Producto externo'),
                categoria=item.get('category', 'general'),
                precio=float(item.get('price', 0)),
                imagen=item.get('thumbnail', ''),
            ).__dict__
            for item in productos[:limite]
        ]
