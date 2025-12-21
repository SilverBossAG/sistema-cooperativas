from django.contrib import admin
from django.urls import path
# Una sola importación limpia:
from usuarios.views import (
    login_view, logout_view, panel_inicio, 
    cambiar_password_obligatorio, listar_vecinos, 
    editar_vecino, crear_vecino, eliminar_vecino
)

urlpatterns = [
    path('admin/', admin.site.urls),          # Panel de admin de Django
    path('', login_view, name='login'),       # La raíz de la web será el login
    path('logout/', logout_view, name='logout'),
    path('inicio/', panel_inicio, name='panel_inicio'), # Donde iremos al entrar
    # --- NUEVAS RUTAS PARA GESTIONAR VECINOS ---
    path('mis-vecinos/', listar_vecinos, name='listar_vecinos'),
    path('crear-vecino/', crear_vecino, name='crear_vecino'),
    path('editar-vecino/<int:id_vecino>/', editar_vecino, name='editar_vecino'),
    path('eliminar-vecino/<int:id_vecino>/', eliminar_vecino, name='eliminar_vecino'),
    path('activar-cuenta/', cambiar_password_obligatorio, name='cambiar_password_obligatorio'),
]