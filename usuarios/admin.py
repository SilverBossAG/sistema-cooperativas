from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cooperativa

class UsuarioAdmin(UserAdmin):
    # 1. FIELDSETS: Añadimos 'numero_vivienda' para poder editarlo dentro de la ficha
    fieldsets = UserAdmin.fieldsets + (
        ('Información Comunidad', {'fields': ('rol', 'cooperativa', 'numero_vivienda', 'requiere_cambio_pass')}),
    )
    
    # 2. LIST_DISPLAY: Añadimos 'numero_vivienda' para verlo en la tabla general
    list_display = ('username', 'email', 'rol', 'cooperativa', 'numero_vivienda', 'requiere_cambio_pass', 'is_staff')
    
    # 3. LIST_FILTER: (Esto lo dejamos igual, filtrar por número de piso no suele ser útil en la barra lateral)
    list_filter = ('rol', 'cooperativa', 'requiere_cambio_pass') 

# Registramos todo
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Cooperativa)