from core.models import Orden, SubOrden, DetalleOrden, EstadoOrden


class OrdenBuilder:
    """
    Construye una Orden paso a paso (Fluent Interface).
    Valida stock y datos antes de llamar a .save().
    """

    def __init__(self):
        self._cliente = None
        self._items = []       # lista de dicts: {variante, cantidad}
        self._cupon = None
        self._errores = []

    # ── Fluent setters ────────────────────────────────────────────────────────

    def para_cliente(self, cliente):
        self._cliente = cliente
        return self

    def con_items(self, items):
        """items: lista de dicts {variante, cantidad}"""
        self._items = items
        return self

    def con_cupon(self, cupon):
        self._cupon = cupon
        return self

    # ── Validaciones ──────────────────────────────────────────────────────────

    def _validar(self):
        if not self._cliente:
            self._errores.append("Cliente requerido.")

        if not self._items:
            self._errores.append("La orden debe tener al menos un item.")

        for entry in self._items:
            variante = entry["variante"]
            cantidad = entry["cantidad"]
            if not variante.validar_stock(cantidad):
                self._errores.append(
                    f"Stock insuficiente para {variante} (pedido: {cantidad}, disponible: {variante.stock})."
                )

        if self._cupon and not self._cupon.es_valido():
            self._errores.append(f"El cupón '{self._cupon.codigo}' no es válido.")

        return len(self._errores) == 0

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self):
        """
        Valida y persiste la Orden con sus SubÓrdenes y DetalleOrden.
        Retorna la Orden creada.
        Lanza ValueError si hay errores de validación.
        """
        if not self._validar():
            raise ValueError(f"Orden inválida: {'; '.join(self._errores)}")

        # Calcular total base
        total = sum(e["variante"].precio * e["cantidad"] for e in self._items)

        # Aplicar descuento del cupón
        descuento = 0
        if self._cupon:
            descuento = self._cupon.calcular_descuento(total)
            self._cupon.usos_disponibles -= 1
            self._cupon.save()

        orden = Orden.objects.create(
            cliente=self._cliente,
            cupon=self._cupon,
            total=total - descuento,
            estado=EstadoOrden.PENDIENTE,
        )

        # Agrupar items por vendedor y crear SubÓrdenes
        grupos = {}
        for entry in self._items:
            vendedor = entry["variante"].producto.vendedor
            grupos.setdefault(vendedor, []).append(entry)

        for vendedor, entries in grupos.items():
            subtotal = sum(e["variante"].precio * e["cantidad"] for e in entries)
            suborden = SubOrden.objects.create(
                orden=orden,
                vendedor=vendedor,
                subtotal=subtotal,
                comision=subtotal * vendedor.comision_pct,
                estado=EstadoOrden.PENDIENTE,
            )
            for entry in entries:
                DetalleOrden.objects.create(
                    suborden=suborden,
                    variante=entry["variante"],
                    cantidad=entry["cantidad"],
                    precio_usuario=entry["variante"].precio,
                )
                # Reducir stock al confirmar
                entry["variante"].reducir_stock(entry["cantidad"])

        return orden