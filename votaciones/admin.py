from django.contrib import admin
from .models import Votacion, Opcion, Voto

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2 # Por defecto muestra hueco para 2 opciones

class VotacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cooperativa', 'fecha_fin', 'activa')
    list_filter = ('cooperativa', 'activa')
    inlines = [OpcionInline] # Permite añadir opciones dentro de la misma pantalla de votación

admin.site.register(Votacion, VotacionAdmin)
admin.site.register(Voto) # Opcional: para ver quién ha votado (cuidado con la privacidad)