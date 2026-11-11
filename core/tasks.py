from celery import shared_task

from core.infra.notificador_factory import NotificadorFactory
from core.models import Orden


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def enviar_confirmacion_orden(orden_id):
    orden = Orden.objects.select_related('cliente').get(pk=orden_id)
    NotificadorFactory.crear().enviar_confirmacion(orden)
    return {'orden_id': orden_id, 'evento': 'confirmacion_enviada'}


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def enviar_cancelacion_orden(orden_id):
    orden = Orden.objects.select_related('cliente').get(pk=orden_id)
    NotificadorFactory.crear().enviar_cancelacion(orden)
    return {'orden_id': orden_id, 'evento': 'cancelacion_enviada'}
