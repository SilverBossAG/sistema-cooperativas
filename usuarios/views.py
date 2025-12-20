from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string 

from .forms import VecinoForm
from .models import Usuario

# --- LOGIN Y LOGOUT ---

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('panel_inicio')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- PANEL PRINCIPAL Y CONTROL DE SEGURIDAD ---

@login_required(login_url='login')
def panel_inicio(request):
    usuario = request.user
    
    if usuario.requiere_cambio_pass:
        return redirect('cambiar_password_obligatorio')

    contexto = {
        'usuario': usuario,
        'cooperativa': usuario.cooperativa
    }

    if usuario.rol == usuario.SUPERADMIN:
        return render(request, 'dashboards/inicio_superadmin.html', context=contexto)
    elif usuario.rol == usuario.PRESIDENTE:
        return render(request, 'dashboards/inicio_presidente.html', context=contexto)
    else: 
        return render(request, 'dashboards/inicio_vecino.html', context=contexto)

@login_required(login_url='login')
def cambiar_password_obligatorio(request):
    if not request.user.requiere_cambio_pass:
        return redirect('panel_inicio')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.requiere_cambio_pass = False
            user.save()
            update_session_auth_hash(request, user)
            return redirect('panel_inicio')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'usuarios/cambiar_pass.html', {'form': form})

# --- GESTIÓN DE VECINOS (SOLO PRESIDENTES) ---

@login_required(login_url='login')
def listar_vecinos(request):
    if request.user.rol != Usuario.PRESIDENTE:
        return redirect('panel_inicio')

    vecinos = Usuario.objects.filter(
        cooperativa=request.user.cooperativa, 
        rol=Usuario.VECINO
    )

    contexto = {
        'vecinos': vecinos,
        'cooperativa': request.user.cooperativa,
        'usuario': request.user
    }
    return render(request, 'dashboards/inicio_presidente.html', context=contexto)

@login_required(login_url='login')
def crear_vecino(request):
    if request.user.rol != Usuario.PRESIDENTE:
        return redirect('panel_inicio')

    if request.method == 'POST':
        form = VecinoForm(request.POST)
        if form.is_valid():
            vecino = form.save(commit=False)
            
            vecino.cooperativa = request.user.cooperativa
            vecino.rol = Usuario.VECINO
            vecino.requiere_cambio_pass = True 

            password_provisional = get_random_string(length=8)
            vecino.set_password(password_provisional)
            vecino.save()

            asunto = 'Bienvenido a tu Comunidad'
            mensaje = f"Usuario: {vecino.username}\nContraseña: {password_provisional}"
            try:
                send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [vecino.email])
            except Exception as e:
                print(f"Error enviando mail: {e}")

            return redirect('listar_vecinos')
    else:
        form = VecinoForm()

    return render(request, 'usuarios/form_vecino.html', {'form': form})

@login_required(login_url='login')
def eliminar_vecino(request, id_vecino):
    vecino = get_object_or_404(Usuario, id=id_vecino, cooperativa=request.user.cooperativa)
    vecino.delete()
    return redirect('panel_inicio')