from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from core.models import Cliente


class RegistroClienteForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Cliente
        fields = ('username', 'email', 'telefono')
        labels = {
            'username': _('Usuario'),
            'email': _('Correo electrónico'),
            'telefono': _('Teléfono'),
        }
