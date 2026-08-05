from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ─── Enumeraciones ────────────────────────────────────────────────────────────

class Genero(models.TextChoices):
    HOMBRE = 'H', 'Hombre'
    MUJER  = 'M', 'Mujer'
    UNISEX = 'U', 'Unisex'


class Talla(models.TextChoices):
    XS = 'XS', 'XS'
    S  = 'S',  'S'
    M  = 'M',  'M'
    L  = 'L',  'L'
    XL = 'XL', 'XL'


class EstadoOrden(models.TextChoices):
    PENDIENTE      = 'PENDIENTE',      'Pendiente'
    PAGADA         = 'PAGADA',         'Pagada'
    EN_PREPARACION = 'EN_PREPARACION', 'En Preparación'
    ENVIADA        = 'ENVIADA',        'Enviada'
    ENTREGADA      = 'ENTREGADA',      'Entregada'
    CANCELADA      = 'CANCELADA',      'Cancelada'


class MetodoPago(models.TextChoices):
    TARJETA  = 'TARJETA',  'Tarjeta'
    PSE      = 'PSE',      'PSE'
    NEQUI    = 'NEQUI',    'Nequi'
    EFECTIVO = 'EFECTIVO', 'Efectivo'


class TipoDescuento(models.TextChoices):
    PORCENTAJE = 'PORCENTAJE', 'Porcentaje'
    MONTO_FIJO = 'MONTO_FIJO', 'Monto Fijo'


# ─── Usuario (base abstracta) ─────────────────────────────────────────────────

class Usuario(AbstractUser):
    """Clase base que extiende el sistema de autenticación de Django."""
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def actualizar_perfil(self, **kwargs):
        for campo, valor in kwargs.items():
            setattr(self, campo, valor)
        self.save()


# ─── Cliente ──────────────────────────────────────────────────────────────────

class Cliente(Usuario):
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def agregar_direccion(self, **datos):
        return Direccion.objects.create(cliente=self, **datos)

    def ver_historial_ordenes(self):
        return self.ordenes.all()


# ─── Vendedor ─────────────────────────────────────────────────────────────────

class Vendedor(Usuario):
    nombre_marca        = models.CharField(max_length=100)
    descripcion         = models.TextField(blank=True)
    ciudad              = models.CharField(max_length=100, blank=True)
    logo                = models.ImageField(upload_to='logos/', blank=True, null=True)
    comision_pct        = models.FloatField(default=0.10)
    calificacion_promedio = models.FloatField(default=0.0)

    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'

    def publicar_producto(self, **datos):
        return Producto.objects.create(vendedor=self, **datos)

    def calcular_liquidacion(self, fecha_inicio, fecha_fin):
        subordenes = self.subordenes.filter(
            orden__fecha__range=(fecha_inicio, fecha_fin),
            orden__estado=EstadoOrden.ENTREGADA,
        )
        return sum(so.subtotal - so.comision for so in subordenes)

    def actualizar_calificacion(self):
        califs = self.calificaciones.all()
        if califs.exists():
            self.calificacion_promedio = califs.aggregate(
                models.Avg('puntaje')
            )['puntaje__avg']
            self.save()


# ─── Dirección ────────────────────────────────────────────────────────────────

class Direccion(models.Model):
    cliente       = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='direcciones')
    calle         = models.CharField(max_length=200)
    ciudad        = models.CharField(max_length=100)
    departamento  = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20, blank=True)
    es_principal  = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'

    def __str__(self):
        return f"{self.calle}, {self.ciudad}"


# ─── Categoría ────────────────────────────────────────────────────────────────

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    genero = models.CharField(max_length=1, choices=Genero.choices)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return f"{self.nombre} ({self.get_genero_display()})"


# ─── Producto ─────────────────────────────────────────────────────────────────

class Producto(models.Model):
    vendedor    = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name='productos')
    categoria   = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    nombre      = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio_base = models.FloatField()

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre

    def agregar_variante(self, **datos):
        return Variante.objects.create(producto=self, **datos)

    def esta_disponible(self):
        return self.variantes.filter(stock__gt=0).exists()

    def precio_final(self):
        """Precio mínimo entre todas las variantes."""
        variantes = self.variantes.all()
        if variantes.exists():
            return min(v.precio for v in variantes)
        return self.precio_base


# ─── Variante (SKU) ───────────────────────────────────────────────────────────

class Variante(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    sku      = models.CharField(max_length=100, unique=True)
    talla    = models.CharField(max_length=2, choices=Talla.choices)
    color    = models.CharField(max_length=50)
    stock    = models.IntegerField(default=0)
    precio   = models.FloatField()

    class Meta:
        verbose_name = 'Variante'
        verbose_name_plural = 'Variantes'
        unique_together = ('producto', 'talla', 'color')

    def __str__(self):
        return f"{self.producto.nombre} — {self.get_talla_display()} {self.color}"

    def validar_stock(self, cant):
        return self.stock >= cant

    def reducir_stock(self, cant):
        if self.validar_stock(cant):
            self.stock -= cant
            self.save()
            return True
        return False

    def reponer_stock(self, cant):
        self.stock += cant
        self.save()


# ─── Cupón ────────────────────────────────────────────────────────────────────

class Cupon(models.Model):
    codigo           = models.CharField(max_length=50, unique=True)
    tipo             = models.CharField(max_length=20, choices=TipoDescuento.choices)
    valor            = models.FloatField()
    fecha_vencimiento = models.DateField()
    compra_minima    = models.FloatField(default=0)
    usos_disponibles = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'

    def __str__(self):
        return self.codigo

    def es_valido(self):
        return (
            self.usos_disponibles > 0 and
            self.fecha_vencimiento >= timezone.now().date()
        )

    def calcular_descuento(self, monto):
        if not self.es_valido() or monto < self.compra_minima:
            return 0
        if self.tipo == TipoDescuento.PORCENTAJE:
            return monto * (self.valor / 100)
        return min(self.valor, monto)


# ─── Carrito ──────────────────────────────────────────────────────────────────

class Carrito(models.Model):
    cliente        = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carrito'

    def agregar_item(self, variante, cant):
        item, creado = ItemCarrito.objects.get_or_create(
            carrito=self,
            variante=variante,
            defaults={'cantidad': cant, 'precio_usuario': variante.precio},
        )
        if not creado:
            item.cantidad += cant
            item.save()
        return item

    def eliminar_item(self, item):
        item.delete()

    def calcular_subtotal(self):
        return sum(item.calcular_subtotal() for item in self.items.all())

    def vaciar(self):
        self.items.all().delete()

    def convertir_en_orden(self):
        orden = Orden.objects.create(cliente=self.cliente, total=self.calcular_subtotal())
        # Agrupar items por vendedor
        grupos = {}
        for item in self.items.select_related('variante__producto__vendedor'):
            vendedor = item.variante.producto.vendedor
            grupos.setdefault(vendedor, []).append(item)

        for vendedor, items in grupos.items():
            subtotal = sum(i.calcular_subtotal() for i in items)
            suborden = SubOrden.objects.create(
                orden=orden,
                vendedor=vendedor,
                subtotal=subtotal,
                comision=subtotal * vendedor.comision_pct,
            )
            for item in items:
                DetalleOrden.objects.create(
                    suborden=suborden,
                    variante=item.variante,
                    cantidad=item.cantidad,
                    precio_usuario=item.precio_usuario,
                )
        self.vaciar()
        return orden


class ItemCarrito(models.Model):
    carrito       = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    variante      = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad      = models.IntegerField(default=1)
    precio_usuario = models.FloatField()

    class Meta:
        verbose_name = 'Item de Carrito'

    def calcular_subtotal(self):
        return self.cantidad * self.precio_usuario


# ─── Orden ────────────────────────────────────────────────────────────────────

class Orden(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordenes')
    cupon   = models.ForeignKey(Cupon, on_delete=models.SET_NULL, null=True, blank=True)
    fecha   = models.DateTimeField(auto_now_add=True)
    estado  = models.CharField(max_length=20, choices=EstadoOrden.choices, default=EstadoOrden.PENDIENTE)
    total   = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'

    def __str__(self):
        return f"Orden #{self.pk} — {self.cliente.username}"

    def calcular_total(self):
        self.total = sum(so.subtotal for so in self.subordenes.all())
        self.save()
        return self.total

    def aplicar_cupon(self, cupon):
        if cupon.es_valido() and self.total >= cupon.compra_minima:
            descuento = cupon.calcular_descuento(self.total)
            self.total -= descuento
            self.cupon = cupon
            cupon.usos_disponibles -= 1
            cupon.save()
            self.save()

    def dividir_por_vendedor(self):
        return self.subordenes.select_related('vendedor').all()

    def procesar_pago(self, metodo):
        pago = Pago.objects.create(orden=self, monto=self.total, metodo=metodo)
        if pago.procesar():
            self.estado = EstadoOrden.PAGADA
            self.save()
            # Reducir stock
            for so in self.subordenes.all():
                for detalle in so.detalles.all():
                    detalle.variante.reducir_stock(detalle.cantidad)
        return pago

    def cancelar(self):
        self.estado = EstadoOrden.CANCELADA
        self.save()


# ─── Pago ─────────────────────────────────────────────────────────────────────

class Pago(models.Model):
    orden              = models.OneToOneField(Orden, on_delete=models.CASCADE, related_name='pago')
    monto              = models.FloatField()
    metodo             = models.CharField(max_length=20, choices=MetodoPago.choices)
    estado             = models.CharField(max_length=50, default='PENDIENTE')
    fecha_vencimiento  = models.DateTimeField(null=True, blank=True)
    fecha              = models.DateTimeField(auto_now_add=True)
    referencia         = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Pago'

    def procesar(self):
        # Aquí se integraría la pasarela de pago real
        self.estado = 'PROCESADO'
        self.save()
        return True

    def reembolsar(self):
        self.estado = 'REEMBOLSADO'
        self.save()
        return True


# ─── SubOrden ─────────────────────────────────────────────────────────────────

class SubOrden(models.Model):
    orden    = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='subordenes')
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name='subordenes')
    estado   = models.CharField(max_length=20, choices=EstadoOrden.choices, default=EstadoOrden.PENDIENTE)
    subtotal = models.FloatField(default=0)
    comision = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Sub-Orden'
        verbose_name_plural = 'Sub-Órdenes'

    def calcular_subtotal(self):
        self.subtotal = sum(d.calcular_subtotal() for d in self.detalles.all())
        self.save()
        return self.subtotal

    def calcular_comision(self):
        self.comision = self.subtotal * self.vendedor.comision_pct
        self.save()
        return self.comision

    def actualizar_estado(self, estado):
        self.estado = estado
        self.save()


# ─── DetalleOrden ─────────────────────────────────────────────────────────────

class DetalleOrden(models.Model):
    suborden      = models.ForeignKey(SubOrden, on_delete=models.CASCADE, related_name='detalles')
    variante      = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad      = models.IntegerField()
    precio_usuario = models.FloatField()

    class Meta:
        verbose_name = 'Detalle de Orden'
        verbose_name_plural = 'Detalles de Orden'

    def calcular_subtotal(self):
        return self.cantidad * self.precio_usuario


# ─── Calificación ─────────────────────────────────────────────────────────────

class Calificacion(models.Model):
    vendedor   = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name='calificaciones')
    cliente    = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='calificaciones')
    puntaje    = models.IntegerField()
    comentario = models.TextField(blank=True)
    fecha      = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ('vendedor', 'cliente')

    def validar(self):
        return 1 <= self.puntaje <= 5