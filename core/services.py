from core.domain.orden_builder import OrdenBuilder
from core.infra.notificador_factory import NotificadorFactory
from django.db import models, transaction

from core.models import (
    Calificacion, Carrito, Cupon, DetalleOrden, EstadoOrden, ItemCarrito,
    MetodoPago, Orden, Pago, Producto, SubOrden, Variante, Vendedor,
)


class OrdenNoEncontrada(Exception):
    """La orden no pertenece al cliente o no existe."""


class OperacionNoPermitida(Exception):
    """La orden no admite la transición solicitada."""


class CatalogoService:
    @staticmethod
    def publicar_producto(vendedor, **datos):
        return Producto.objects.create(vendedor=vendedor, **datos)

    @staticmethod
    def agregar_variante(producto, **datos):
        return Variante.objects.create(producto=producto, **datos)

    @staticmethod
    def esta_disponible(producto):
        return producto.variantes.filter(stock__gt=0).exists()

    @staticmethod
    def precio_final(producto):
        precios = producto.variantes.values_list('precio', flat=True)
        return min(precios) if precios else producto.precio_base

    @staticmethod
    def agregar_direccion(cliente, **datos):
        from core.models import Direccion
        return Direccion.objects.create(cliente=cliente, **datos)

    @staticmethod
    def actualizar_perfil(usuario, **kwargs):
        for campo, valor in kwargs.items():
            setattr(usuario, campo, valor)
        usuario.save()


class CarritoService:
    @staticmethod
    def agregar_item(carrito, variante, cantidad):
        item, creado = ItemCarrito.objects.get_or_create(
            carrito=carrito, variante=variante,
            defaults={'cantidad': cantidad, 'precio_usuario': variante.precio},
        )
        if not creado:
            item.cantidad += cantidad
            item.save(update_fields=('cantidad',))
        return item

    @staticmethod
    def calcular_subtotal(carrito):
        return sum(item.cantidad * item.precio_usuario for item in carrito.items.all())

    @staticmethod
    def vaciar(carrito):
        carrito.items.all().delete()

    @classmethod
    def convertir_en_orden(cls, carrito):
        items = list(carrito.items.select_related('variante__producto__vendedor'))
        orden_items = [
            {'variante': item.variante, 'cantidad': item.cantidad} for item in items
        ]
        orden = OrdenService().procesar_orden(carrito.cliente, orden_items)
        cls.vaciar(carrito)
        return orden


class VendedorService:
    @staticmethod
    def calcular_liquidacion(vendedor, fecha_inicio, fecha_fin):
        subordenes = vendedor.subordenes.filter(
            orden__fecha__range=(fecha_inicio, fecha_fin),
            orden__estado=EstadoOrden.ENTREGADA,
        )
        return sum(suborden.subtotal - suborden.comision for suborden in subordenes)

    @staticmethod
    def actualizar_calificacion(vendedor):
        promedio = vendedor.calificaciones.aggregate(models.Avg('puntaje'))['puntaje__avg']
        if promedio is not None:
            vendedor.calificacion_promedio = promedio
            vendedor.save(update_fields=('calificacion_promedio',))


class PagoService:
    @staticmethod
    def procesar(pago):
        pago.estado = 'PROCESADO'
        pago.save(update_fields=('estado',))
        return True

    @staticmethod
    def reembolsar(pago):
        pago.estado = 'REEMBOLSADO'
        pago.save(update_fields=('estado',))
        return True


class CalificacionService:
    @staticmethod
    def validar_puntaje(puntaje):
        return 1 <= puntaje <= 5


class OrdenQueryService:
    @staticmethod
    def historial(cliente):
        return cliente.ordenes.all()


class OrdenService:
    """
    Capa de aplicación: orquesta el flujo de creación de una Orden.
    Aplica Inyección de Dependencias — el notificador se inyecta desde afuera
    (o se crea con la Factory si no se provee uno).
    """

    def __init__(self, notificador=None):
        self.notificador = notificador or NotificadorFactory.crear()

    def procesar_orden(self, cliente, items, cupon=None):
        """
        Flujo principal:
        1. Construye y valida la Orden con OrdenBuilder.
        2. Notifica al cliente.
        3. Retorna la Orden creada.

        Parámetros:
            cliente  : instancia de Cliente
            items    : lista de dicts {variante: Variante, cantidad: int}
            cupon    : instancia de Cupon (opcional)

        Retorna:
            Orden creada y persistida.

        Lanza:
            ValueError si la validación falla (stock insuficiente, cupón inválido, etc.)
        """
        orden = (
            OrdenBuilder()
            .para_cliente(cliente)
            .con_items(items)
            .con_cupon(cupon)
            .build()
        )

        self.notificador.enviar_confirmacion(orden)

        return orden

    def crear_desde_ids(self, cliente, items, cupon_codigo=''):
        variantes = []
        for item in items:
            variante = Variante.objects.select_related('producto__vendedor').get(
                pk=item['variante']
            )
            variantes.append({'variante': variante, 'cantidad': item['cantidad']})

        cupon = None
        if cupon_codigo:
            cupon = Cupon.objects.filter(codigo=cupon_codigo).first()
            if cupon is None:
                raise ValueError('El cupón indicado no existe.')

        return self.procesar_orden(cliente, variantes, cupon)

    def obtener_orden(self, cliente, orden_id):
        try:
            return Orden.objects.prefetch_related(
                'subordenes__detalles'
            ).get(pk=orden_id, cliente=cliente)
        except Orden.DoesNotExist as exc:
            raise OrdenNoEncontrada('La orden no existe.') from exc

    def listar_ordenes(self, cliente):
        return Orden.objects.filter(cliente=cliente).prefetch_related(
            'subordenes__detalles'
        ).order_by('-fecha')

    @transaction.atomic
    def procesar_pago(self, cliente, orden_id, metodo):
        orden = self.obtener_orden(cliente, orden_id)
        if orden.estado != EstadoOrden.PENDIENTE:
            raise OperacionNoPermitida('Solo se puede pagar una orden pendiente.')
        if metodo not in MetodoPago.values:
            raise ValueError('Método de pago inválido.')
        pago = Pago.objects.create(orden=orden, monto=orden.total, metodo=metodo)
        if not PagoService.procesar(pago):
            raise OperacionNoPermitida('El pago no pudo ser procesado.')
        orden.estado = EstadoOrden.PAGADA
        orden.save(update_fields=('estado',))
        return pago

    def cancelar_orden(self, cliente, orden_id):
        orden = self.obtener_orden(cliente, orden_id)
        if orden.estado != EstadoOrden.PENDIENTE:
            raise OperacionNoPermitida('Solo se puede cancelar una orden pendiente.')
        orden.estado = EstadoOrden.CANCELADA
        orden.save(update_fields=('estado',))
        self.notificador.enviar_cancelacion(orden)
        return orden