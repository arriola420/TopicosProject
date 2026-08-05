from core.domain.orden_builder import OrdenBuilder
from core.infra.notificador_factory import NotificadorFactory


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