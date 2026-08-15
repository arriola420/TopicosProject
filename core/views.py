from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from core.models import Variante, Cupon
from core.services import OrdenService


@method_decorator(csrf_exempt, name='dispatch')
class ProcesarOrdenView(View):
    """
    Capa de Interfaz: solo captura datos del request y delega al Service.
    Responsabilidad única: HTTP in → HTTP out.
    """

    def post(self, request):
        try:
            items = self._extraer_items(request.POST)
            cupon = self._extraer_cupon(request.POST.get("cupon_codigo"))
            cliente = request.user.cliente
            orden = OrdenService().procesar_orden(cliente, items, cupon)
            return JsonResponse({"ok": True, "orden_id": orden.id}, status=201)
        except (ValueError, ObjectDoesNotExist) as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    @staticmethod
    def _extraer_items(post):
        """Convierte los datos del POST en lista de {variante, cantidad}."""
        variante_ids = post.getlist("variante_id")
        cantidades   = post.getlist("cantidad")
        if len(variante_ids) != len(cantidades):
            raise ValueError("Cada variante debe tener una cantidad.")
        return [
            {"variante": Variante.objects.get(pk=vid), "cantidad": int(cant)}
            for vid, cant in zip(variante_ids, cantidades)
        ]

    @staticmethod
    def _extraer_cupon(codigo):
        if not codigo:
            return None
        return Cupon.objects.filter(codigo=codigo).first()
