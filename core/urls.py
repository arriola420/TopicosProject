from django.urls import path

from core.views import ProcesarOrdenView


app_name = 'core'

urlpatterns = [
    path('ordenes/', ProcesarOrdenView.as_view(), name='procesar-orden'),
]
