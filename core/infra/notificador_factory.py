import os

from django.conf import settings
from django.core.mail import send_mail


# ── Implementaciones de Notificador ───────────────────────────────────────────

class NotificadorMock:
    """Usado en desarrollo: imprime en consola en lugar de enviar emails."""

    def enviar_confirmacion(self, orden):
        print(f"[MOCK] Confirmación de orden #{orden.id} enviada a {orden.cliente.email}")

    def enviar_cancelacion(self, orden):
        print(f"[MOCK] Cancelación de orden #{orden.id} notificada a {orden.cliente.email}")


class NotificadorEmail:
    """Usado en producción con el backend de correo configurado en Django."""

    def enviar_confirmacion(self, orden):
        return send_mail(
            f"Confirmación de orden #{orden.id}",
            f"Tu orden #{orden.id} fue creada correctamente.",
            settings.DEFAULT_FROM_EMAIL,
            [orden.cliente.email],
        )

    def enviar_cancelacion(self, orden):
        return send_mail(
            f"Cancelación de orden #{orden.id}",
            f"Tu orden #{orden.id} fue cancelada.",
            settings.DEFAULT_FROM_EMAIL,
            [orden.cliente.email],
        )


# ── Factory ───────────────────────────────────────────────────────────────────

class NotificadorFactory:
    """
    Decide qué implementación de Notificador usar según la variable de entorno
    NOTIFICADOR_TYPE:
        MOCK  → NotificadorMock  (desarrollo/testing)
        REAL  → NotificadorEmail (producción)
    """

    @staticmethod
    def crear():
        tipo = os.getenv("NOTIFICADOR_TYPE", "MOCK").upper()

        if tipo == "REAL":
            return NotificadorEmail()

        return NotificadorMock()
