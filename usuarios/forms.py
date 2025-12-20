from django import forms
from .models import Usuario

class VecinoForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # YA NO PEDIMOS PASSWORD. Solo datos de contacto.
        fields = ['username', 'first_name', 'last_name', 'email']