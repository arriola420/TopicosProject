from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import CrearOrdenSerializer, OrdenSerializer
from core.services import OperacionNoPermitida, OrdenNoEncontrada, OrdenService


class HomeView(TemplateView):
    template_name = 'core/home.html'


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
                {'detail': 'Una de las variantes no existe.'},
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
                {'detail': 'El método de pago es requerido.'},
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
