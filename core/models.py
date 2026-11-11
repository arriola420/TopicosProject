from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


# ─── Enumeraciones ────────────────────────────────────────────────────────────

class Genero(models.TextChoices):
    HOMBRE = 'H', _('Hombre')
    MUJER  = 'M', _('Mujer')
    UNISEX = 'U', _('Unisex')


class Talla(models.TextChoices):
    XS = 'XS', 'XS'
    S  = 'S',  'S'
    M  = 'M',  'M'
    L  = 'L',  'L'
    XL = 'XL', 'XL'


class EstadoOrden(models.TextChoices):
    PENDIENTE      = 'PENDIENTE',      _('Pendiente')
    PAGADA         = 'PAGADA',         _('Pagada')
    EN_PREPARACION = 'EN_PREPARACION', _('En preparación')
    ENVIADA        = 'ENVIADA',        _('Enviada')
    ENTREGADA      = 'ENTREGADA',      _('Entregada')
    CANCELADA      = 'CANCELADA',      _('Cancelada')


class MetodoPago(models.TextChoices):
    TARJETA  = 'TARJETA',  _('Tarjeta')
    PSE      = 'PSE',      'PSE'
    NEQUI    = 'NEQUI',    'Nequi'
    EFECTIVO = 'EFECTIVO', _('Efectivo')


class TipoDescuento(models.TextChoices):
    PORCENTAJE = 'PORCENTAJE', _('Porcentaje')
    MONTO_FIJO = 'MONTO_FIJO', _('Monto fijo')


# ─── Usuario (base abstracta) ─────────────────────────────────────────────────

class Usuario(AbstractUser):
    """Clase base que extiende el sistema de autenticación de Django."""
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

# ─── Cliente ──────────────────────────────────────────────────────────────────

class Cliente(Usuario):
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

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
    imagen_url  = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre

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

# ─── Carrito ──────────────────────────────────────────────────────────────────

class Carrito(models.Model):
    cliente        = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carrito'

class ItemCarrito(models.Model):
    carrito       = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    variante      = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad      = models.IntegerField(default=1)
    precio_usuario = models.FloatField()

    class Meta:
        verbose_name = 'Item de Carrito'

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

# ─── DetalleOrden ─────────────────────────────────────────────────────────────

class DetalleOrden(models.Model):
    suborden      = models.ForeignKey(SubOrden, on_delete=models.CASCADE, related_name='detalles')
    variante      = models.ForeignKey(Variante, on_delete=models.CASCADE)
    cantidad      = models.IntegerField()
    precio_usuario = models.FloatField()

    class Meta:
        verbose_name = 'Detalle de Orden'
        verbose_name_plural = 'Detalles de Orden'

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

