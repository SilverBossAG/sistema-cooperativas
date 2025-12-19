from django.contrib import admin
from django.urls import path
from usuarios.views import login_view, logout_view, panel_inicio # Importamos nuestras vistas
from django.shortcuts import render


urlpatterns = [
    path('admin/', admin.site.urls),          # Panel de admin de Django
    path('', login_view, name='login'),       # La raíz de la web será el login
    path('logout/', logout_view, name='logout'),
    path('inicio/', panel_inicio, name='panel_inicio'), # Donde iremos al entrar
]