from django.urls import path

from core.views import CancelarOrdenView, OrdenDetalleView, OrdenesView, PagarOrdenView


app_name = 'core'

urlpatterns = [
    path('ordenes/', OrdenesView.as_view(), name='procesar-orden'),
    path('ordenes/', OrdenesView.as_view(), name='ordenes'),
    path('ordenes/<int:orden_id>/', OrdenDetalleView.as_view(), name='orden-detalle'),
    path('ordenes/<int:orden_id>/pagar/', PagarOrdenView.as_view(), name='pagar-orden'),
    path('ordenes/<int:orden_id>/cancelar/', CancelarOrdenView.as_view(), name='cancelar-orden'),
]
