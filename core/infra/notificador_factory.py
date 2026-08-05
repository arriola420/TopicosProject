import os


# ── Implementaciones de Notificador ───────────────────────────────────────────

class NotificadorMock:
    """Usado en desarrollo: imprime en consola en lugar de enviar emails."""

    def enviar_confirmacion(self, orden):
        print(f"[MOCK] Confirmación de orden #{orden.id} enviada a {orden.cliente.email}")

    def enviar_cancelacion(self, orden):
        print(f"[MOCK] Cancelación de orden #{orden.id} notificada a {orden.cliente.email}")


class NotificadorEmail:
    """Usado en producción: enviaría el email real (ej: SendGrid, SES)."""

    def enviar_confirmacion(self, orden):
        # Aquí iría la integración real con el servicio de email
        # send_mail(subject, message, from, [orden.cliente.email])
        raise NotImplementedError("Integrar con servicio de email real (SendGrid, SES, etc.)")

    def enviar_cancelacion(self, orden):
        raise NotImplementedError("Integrar con servicio de email real.")


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