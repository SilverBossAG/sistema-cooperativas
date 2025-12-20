from django.contrib import admin
from django.urls import path
from usuarios.views import login_view, logout_view, panel_inicio # Importamos nuestras vistas
from django.shortcuts import render
from usuarios.views import cambiar_password_obligatorio, login_view, logout_view, panel_inicio, listar_vecinos, crear_vecino, eliminar_vecino


urlpatterns = [
    path('admin/', admin.site.urls),          # Panel de admin de Django
    path('', login_view, name='login'),       # La raíz de la web será el login
    path('logout/', logout_view, name='logout'),
    path('inicio/', panel_inicio, name='panel_inicio'), # Donde iremos al entrar
    # --- NUEVAS RUTAS PARA GESTIONAR VECINOS ---
    path('mis-vecinos/', listar_vecinos, name='listar_vecinos'),
    path('crear-vecino/', crear_vecino, name='crear_vecino'),
    path('eliminar-vecino/<int:id_vecino>/', eliminar_vecino, name='eliminar_vecino'),
    path('activar-cuenta/', cambiar_password_obligatorio, name='cambiar_password_obligatorio'),
]