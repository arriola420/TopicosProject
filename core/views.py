from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.forms import RegistroClienteForm
from core.integrations import (
    CatalogoExternoAdapter,
    IntegracionNoDisponible,
    ServicioAliadoAdapter,
)
from core.models import Producto
from core.serializers import CrearOrdenSerializer, OrdenSerializer
from core.services import OperacionNoPermitida, OrdenNoEncontrada, OrdenService


class HomeView(TemplateView):
    template_name = 'core/home.html'


class RegistroClienteView(FormView):
    template_name = 'core/registro.html'
    form_class = RegistroClienteForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        usuario = form.save()
        login(self.request, usuario)
        return redirect(self.get_success_url())


class CatalogoPublicoView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        productos = []
        queryset = Producto.objects.select_related('vendedor', 'categoria').prefetch_related(
            'variantes'
        ).order_by('nombre')
        for producto in queryset:
            productos.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'imagen': producto.imagen_url,
                'vendedor': producto.vendedor.nombre_marca,
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'variantes': [
                    {
                        'id': variante.id,
                        'sku': variante.sku,
                        'talla': variante.get_talla_display(),
                        'color': variante.color,
                        'stock': variante.stock,
                        'precio': variante.precio,
                    }
                    for variante in producto.variantes.all()
                ],
            })
        return Response({
            'servicio': 'Marketplace Catalog API v1',
            'productos': productos,
        })


class ServicioAliadoView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            return Response(ServicioAliadoAdapter().obtener_informacion())
        except IntegracionNoDisponible as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class RecomendacionesExternasView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            productos = CatalogoExternoAdapter().obtener_recomendaciones()
            return Response({
                'fuente': 'API externa mediante CatalogoExternoAdapter',
                'productos': productos,
            })
        except IntegracionNoDisponible as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class OrdenesView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _datos_de_entrada(request):
        if 'items' in request.data:
            return request.data
        variante_ids = request.data.getlist('variante_id')
        cantidades = request.data.getlist('cantidad')
        return {
            'items': [
                {'variante': variante_id, 'cantidad': cantidad}
                for variante_id, cantidad in zip(variante_ids, cantidades)
            ],
            'cupon_codigo': request.data.get('cupon_codigo', ''),
        }

    def get(self, request):
        ordenes = OrdenService().listar_ordenes(request.user.cliente)
        return Response(OrdenSerializer(ordenes, many=True).data)

    def post(self, request):
        serializer = CrearOrdenSerializer(data=self._datos_de_entrada(request))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            orden = OrdenService().crear_desde_ids(
                request.user.cliente,
                serializer.validated_data['items'],
                serializer.validated_data.get('cupon_codigo', ''),
            )
        except ObjectDoesNotExist:
            return Response(
                {'detail': _('Una de las variantes no existe.')},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {'ok': True, 'orden_id': orden.id, 'orden': OrdenSerializer(orden).data},
            status=status.HTTP_201_CREATED,
        )


class OrdenDetalleView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, orden_id):
        try:
            orden = OrdenService().obtener_orden(request.user.cliente, orden_id)
        except OrdenNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrdenSerializer(orden).data)


class PagarOrdenView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, orden_id):
        metodo = request.data.get('metodo')
        if not metodo:
            return Response(
                {'detail': _('El método de pago es requerido.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            OrdenService().procesar_pago(request.user.cliente, orden_id, metodo)
            orden = OrdenService().obtener_orden(request.user.cliente, orden_id)
        except OrdenNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except (OperacionNoPermitida, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(OrdenSerializer(orden).data)


class CancelarOrdenView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, orden_id):
        try:
            orden = OrdenService().cancelar_orden(request.user.cliente, orden_id)
        except OrdenNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except OperacionNoPermitida as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(OrdenSerializer(orden).data)
