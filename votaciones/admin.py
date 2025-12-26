from django.contrib import admin
from .models import Votacion, Opcion, Voto

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 2 # Por defecto muestra hueco para 2 opciones

class VotacionAdmin(admin.ModelAdmin):
    # En list_display SÍ funciona (porque solo es mostrar)
    list_display = ('titulo', 'cooperativa', 'fecha_fin', 'activa')
    
    # En list_filter NO funciona directamente (porque requiere cálculos), así que lo quitamos
    list_filter = ('cooperativa',) 
    
    inlines = [OpcionInline]

admin.site.register(Votacion, VotacionAdmin)
admin.site.register(Voto)