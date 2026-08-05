from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Cliente, Vendedor,
    Direccion, Categoria, Producto, Variante,
    Carrito, ItemCarrito,
    Cupon, Orden, SubOrden, DetalleOrden, Pago,
    Calificacion,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'telefono', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Extra', {'fields': ('telefono',)}),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'telefono')


class VarianteInline(admin.TabularInline):
    model = Variante
    extra = 1


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('username', 'nombre_marca', 'ciudad', 'comision_pct', 'calificacion_promedio')


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'calle', 'ciudad', 'es_principal')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'genero')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'vendedor', 'categoria', 'precio_base')
    inlines = [VarianteInline]


@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    list_display = ('sku', 'producto', 'talla', 'color', 'stock', 'precio')


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'valor', 'fecha_vencimiento', 'usos_disponibles')


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_creacion')
    inlines = [ItemCarritoInline]


class SubOrdenInline(admin.TabularInline):
    model = SubOrden
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'estado', 'total', 'fecha')
    list_filter = ('estado',)
    inlines = [SubOrdenInline]


class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrden
    extra = 0


@admin.register(SubOrden)
class SubOrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'orden', 'vendedor', 'estado', 'subtotal', 'comision')
    inlines = [DetalleOrdenInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('orden', 'metodo', 'monto', 'estado', 'fecha')


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('vendedor', 'cliente', 'puntaje', 'fecha')