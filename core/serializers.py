from rest_framework import serializers

from core.models import DetalleOrden, Orden, SubOrden


class ItemOrdenInputSerializer(serializers.Serializer):
    variante = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class CrearOrdenSerializer(serializers.Serializer):
    items = ItemOrdenInputSerializer(many=True, allow_empty=False)
    cupon_codigo = serializers.CharField(required=False, allow_blank=True)


class DetalleOrdenSerializer(serializers.ModelSerializer):
    variante = serializers.IntegerField(source='variante_id')

    class Meta:
        model = DetalleOrden
        fields = ('variante', 'cantidad', 'precio_usuario')


class SubOrdenSerializer(serializers.ModelSerializer):
    vendedor = serializers.IntegerField(source='vendedor_id')
    detalles = DetalleOrdenSerializer(many=True, read_only=True)

    class Meta:
        model = SubOrden
        fields = ('id', 'vendedor', 'estado', 'subtotal', 'comision', 'detalles')


class OrdenSerializer(serializers.ModelSerializer):
    cupon = serializers.CharField(source='cupon.codigo', read_only=True, allow_null=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    subordenes = SubOrdenSerializer(many=True, read_only=True)

    class Meta:
        model = Orden
        fields = ('id', 'fecha', 'estado', 'estado_display', 'total', 'cupon', 'subordenes')
