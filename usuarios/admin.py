from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cooperativa  # <--- Importamos AMBOS modelos

class UsuarioAdmin(UserAdmin):
    # fieldsets: Controla qué campos ves al editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        # Añadimos tanto el ROL como la COOPERATIVA
        ('Información Comunidad', {'fields': ('rol', 'cooperativa')}),
    )
    
    # list_display: Controla las columnas de la tabla de usuarios
    list_display = ('username', 'email', 'rol', 'cooperativa', 'is_staff')
    
    # list_filter: Añade un filtro lateral para buscar rápido por edificio o rol
    list_filter = ('rol', 'cooperativa') 

# Registramos el Usuario con la configuración nueva
admin.site.register(Usuario, UsuarioAdmin)

# ¡IMPORTANTE! Registramos la Cooperativa para que aparezca en el panel
admin.site.register(Cooperativa)