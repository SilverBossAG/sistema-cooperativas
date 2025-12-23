from django import forms
from .models import Votacion

class VotacionForm(forms.ModelForm):
    class Meta:
        model = Votacion
        fields = ['titulo', 'descripcion', 'fecha_fin']
        # Esto hace que el navegador muestre un calendario para elegir la fecha
        widgets = {
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

