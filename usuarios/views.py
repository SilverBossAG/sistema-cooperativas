from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token # Necesario para Jinja2
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string # Para generar la pass

from .forms import VecinoForm
from .models import Usuario

def login_view(request):
    # CASO 1: POST
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('panel_inicio')
    
    # CASO 2: GET
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'csrf_token': get_token(request), 
    }
    return render(request, 'login.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

# --- FUNCIONES DE INICIO Y SEGURIDAD ---

@login_required(login_url='login')
def panel_inicio(request):
    usuario = request.user
    
    # 1. INTERCEPTOR DE SEGURIDAD
    # Si tiene la marca activada, LO OBLIGAMOS a ir a cambiar contraseña
    if usuario.requiere_cambio_pass:
        return redirect('cambiar_password_obligatorio')

    # Preparamos los datos
    contexto = {
        'usuario': usuario,
        'cooperativa': usuario.cooperativa
    }

    # Redirección según ROL
    if usuario.rol == usuario.SUPERADMIN:
        return render(request, 'dashboards/inicio_superadmin.html', context=contexto)

    elif usuario.rol == usuario.PRESIDENTE:
        return render(request, 'dashboards/inicio_presidente.html', context=contexto)

    else: # VECINO
        return render(request, 'dashboards/inicio_vecino.html', context=contexto)

# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
@login_required(login_url='login')
def cambiar_password_obligatorio(request):
    # Si el usuario ya la cambió, lo echamos fuera (al inicio)
    if not request.user.requiere_cambio_pass:
        return redirect('panel_inicio')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # IMPORTANTE: Marcamos que YA CUMPLIÓ y guardamos
            user.requiere_cambio_pass = False
            user.save()
            # Mantenemos la sesión activa para que no tenga que loguearse de nuevo
            update_session_auth_hash(request, user)
            return redirect('panel_inicio')
    else:
        form = PasswordChangeForm(request.user)
    
    # Pasamos el csrf_token para Jinja2
    return render(request, 'usuarios/cambiar_pass.html', {'form': form, 'csrf_token': get_token(request)})

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
            
            # Configuración automática
            vecino.cooperativa = request.user.cooperativa
            vecino.rol = Usuario.VECINO
            vecino.requiere_cambio_pass = True  # ¡OBLIGATORIO!

            # Generar contraseña
            password_provisional = get_random_string(length=8)
            vecino.set_password(password_provisional)
            
            vecino.save()

            # Enviar Email
            asunto = 'Bienvenido a tu Comunidad - Datos de Acceso'
            mensaje = f"""
            Hola {vecino.username},
            
            El presidente te ha dado de alta en la plataforma de {vecino.cooperativa.nombre}.
            
            Tus datos de acceso son:
            Usuario: {vecino.username}
            Contraseña temporal: {password_provisional}
            
            Por favor, entra y cambia tu contraseña inmediatamente.
            """
            try:
                send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [vecino.email])
            except Exception as e:
                print(f"Error enviando mail: {e}")

            return redirect('listar_vecinos')
    else:
        form = VecinoForm()

    # Añadido csrf_token por seguridad con Jinja2
    return render(request, 'usuarios/form_vecino.html', {'form': form, 'csrf_token': get_token(request)})

@login_required(login_url='login')
def eliminar_vecino(request, id_vecino):
    vecino = get_object_or_404(Usuario, id=id_vecino, cooperativa=request.user.cooperativa)
    vecino.delete()
    return redirect('panel_inicio')