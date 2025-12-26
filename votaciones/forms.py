from django import forms
from .models import Votacion

class VotacionForm(forms.ModelForm):
    class Meta:
        model = Votacion
        fields = ['titulo', 'descripcion', 'fecha_fin']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Derrama Tejado'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # AQUÍ ACTIVAMOS EL SELECTOR DE HORA Y SEGUNDOS
            'fecha_fin': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'step': '1'  # Permite elegir segundos
            }),
        }