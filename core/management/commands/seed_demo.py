from django.core.management.base import BaseCommand

from core.models import Categoria, Genero, Producto, Talla, Variante, Vendedor


class Command(BaseCommand):
    help = 'Crea un catálogo demostrativo idempotente para validar la interfaz.'

    def handle(self, *args, **options):
        vendedor, creado = Vendedor.objects.get_or_create(
            username='marca_nomada',
            defaults={
                'email': 'marca@nomada.local',
                'nombre_marca': 'Taller Nómada',
                'descripcion': 'Diseño independiente de producción local.',
                'ciudad': 'Medellín',
            },
        )
        if creado:
            vendedor.set_unusable_password()
            vendedor.save(update_fields=('password',))

        categoria, _ = Categoria.objects.get_or_create(
            nombre='Esenciales', defaults={'genero': Genero.UNISEX}
        )
        catalogo = [
            ('Camiseta Horizonte', 'HORIZONTE-M', 'Arena', Talla.M, 89000,
             'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80'),
            ('Chaqueta Bruma', 'BRUMA-L', 'Oliva', Talla.L, 219000,
             'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=900&q=80'),
            ('Bolso Sendero', 'SENDERO-U', 'Terracota', Talla.M, 139000,
             'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80'),
        ]
        for nombre, sku, color, talla, precio, imagen_url in catalogo:
            producto, _ = Producto.objects.get_or_create(
                vendedor=vendedor,
                nombre=nombre,
                defaults={
                    'categoria': categoria,
                    'descripcion': 'Pieza versátil creada en series pequeñas.',
                    'precio_base': precio,
                },
            )
            producto.imagen_url = imagen_url
            producto.save(update_fields=('imagen_url',))
            variante, variante_creada = Variante.objects.get_or_create(
                sku=sku,
                defaults={
                    'producto': producto,
                    'talla': talla,
                    'color': color,
                    'stock': 12,
                    'precio': precio,
                },
            )
            if not variante_creada:
                variante.producto = producto
                variante.talla = talla
                variante.color = color
                variante.precio = precio
                variante.save(update_fields=('producto', 'talla', 'color', 'precio'))
        self.stdout.write(self.style.SUCCESS('Catálogo demo disponible.'))
