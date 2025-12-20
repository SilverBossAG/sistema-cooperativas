from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cooperativa

class UsuarioAdmin(UserAdmin):
    # 1. FIELDSETS: Para que aparezca la cajita cuando entras a editar al usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información Comunidad', {'fields': ('rol', 'cooperativa', 'requiere_cambio_pass')}),
    )
    
    # 2. LIST_DISPLAY:
    list_display = ('username', 'email', 'rol', 'cooperativa', 'requiere_cambio_pass', 'is_staff')
    
    # 3. LIST_FILTER: Para filtrar a la derecha por usuarios que deben cambiar pass
    list_filter = ('rol', 'cooperativa', 'requiere_cambio_pass') 

# Registramos todo
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Cooperativa)