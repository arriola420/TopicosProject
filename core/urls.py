from django.urls import path

from core.views import (
    CancelarOrdenView,
    CatalogoPublicoView,
    OrdenDetalleView,
    OrdenesView,
    PagarOrdenView,
    RecomendacionesExternasView,
    ServicioAliadoView,
)


app_name = 'core'

urlpatterns = [
    path('ordenes/', OrdenesView.as_view(), name='procesar-orden'),
    path('ordenes/', OrdenesView.as_view(), name='ordenes'),
    path('ordenes/<int:orden_id>/', OrdenDetalleView.as_view(), name='orden-detalle'),
    path('ordenes/<int:orden_id>/pagar/', PagarOrdenView.as_view(), name='pagar-orden'),
    path('ordenes/<int:orden_id>/cancelar/', CancelarOrdenView.as_view(), name='cancelar-orden'),
    path('integracion/catalogo/', CatalogoPublicoView.as_view(), name='catalogo-publico'),
    path('integracion/aliado/', ServicioAliadoView.as_view(), name='servicio-aliado'),
    path(
        'integracion/recomendaciones/',
        RecomendacionesExternasView.as_view(),
        name='recomendaciones-externas',
    ),
]
