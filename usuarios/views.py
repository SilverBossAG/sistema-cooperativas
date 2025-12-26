from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string 
from .forms import VecinoForm
from .models import Usuario
import random 
from django.contrib import messages 
from votaciones.models import Votacion, Voto

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
    
    # 1. INTERCEPTOR DE SEGURIDAD
    if usuario.requiere_cambio_pass:
        return redirect('cambiar_password_obligatorio')

    # 2. CÁLCULO DE VOTACIONES PENDIENTES (Solo para vecinos/presidentes)
    pendientes_count = 0
    if usuario.cooperativa:
        # A. Buscamos todas las votaciones ACTIVAS de su comunidad
        # CORRECCIÓN AQUÍ: Usamos fecha_fin__gt en lugar de activa=True
        votaciones_activas = Votacion.objects.filter(
            cooperativa=usuario.cooperativa, 
            fecha_fin__gt=timezone.now()
        )
        
        # B. Buscamos en cuáles YA ha votado este usuario
        votos_usuario = Voto.objects.filter(
            usuario=usuario,
            votacion__in=votaciones_activas
        ).values_list('votacion_id', flat=True)
        
        # C. Restamos: (Total Activas) - (Votadas) = Pendientes
        # Filtramos las activas excluyendo las que ya están en 'votos_usuario'
        pendientes_count = votaciones_activas.exclude(id__in=votos_usuario).count()

    # Preparamos los datos
    contexto = {
        'usuario': usuario,
        'cooperativa': usuario.cooperativa,
        'pendientes': pendientes_count, 
    }

    # Redirección según ROL
    if usuario.rol == usuario.SUPERADMIN:
        return render(request, 'dashboards/inicio_superadmin.html', context=contexto)

    elif usuario.rol == usuario.PRESIDENTE:
        return render(request, 'dashboards/inicio_presidente.html', context=contexto)

    else: # VECINO
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
    return render(request, 'dashboards/gestion_vecinos.html', context=contexto)


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
def editar_vecino(request, id_vecino):
    # 1. Seguridad: Solo presidentes
    if request.user.rol != Usuario.PRESIDENTE:
        return redirect('panel_inicio')

    # 2. Buscar al vecino (Asegurándonos de que sea de SU cooperativa)
    vecino = get_object_or_404(Usuario, id=id_vecino, cooperativa=request.user.cooperativa)

    if request.method == 'POST':
        # Cargar el formulario con los datos que envía el presidente (POST)
        # 'instance=vecino' es la CLAVE: le dice a Django que no cree uno nuevo, sino que actualice este.
        form = VecinoForm(request.POST, instance=vecino)
        
        if form.is_valid():
            form.save()
            return redirect('listar_vecinos')
    else:
        # Si entra por primera vez, le mostramos el formulario RELLENO con los datos actuales
        form = VecinoForm(instance=vecino)

    return render(request, 'usuarios/form_editar_vecino.html', {'form': form, 'vecino': vecino})


@login_required(login_url='login')
def eliminar_vecino(request, id_vecino):
    vecino = get_object_or_404(Usuario, id=id_vecino, cooperativa=request.user.cooperativa)
    vecino.delete()
    return redirect('listar_vecinos')


# --- GESTIÓN DEL PERFIL VECINO (vecinos)---

@login_required(login_url='login')
def ver_perfil(request):
    # Solo mostramos los datos, no dejamos editar aquí
    return render(request, 'usuarios/perfil.html', {'usuario': request.user})

@login_required(login_url='login')
def solicitar_codigo_perfil(request):
    usuario = request.user
    
    # 1. Generamos un código de 6 dígitos
    codigo = str(random.randint(100000, 999999))
    
    # 2. Guardamos el código en la "memoria" de la sesión del usuario
    request.session['codigo_seguridad'] = codigo
    
    # 3. Enviamos el email
    asunto = 'Código de Seguridad - Editar Perfil'
    mensaje = f"""
    Hola {usuario.username},
    
    Has solicitado editar tu perfil. Tu código de seguridad es:
    
    {codigo}
    
    Si no has sido tú, ignora este mensaje y cambia tu contraseña por seguridad.
    """
    try:
        send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [usuario.email])
        print(f"--- CÓDIGO GENERADO: {codigo} ---") # Para que lo veas en la terminal si falla el email
    except Exception as e:
        print(f"Error enviando mail: {e}")

    # 4. Le mandamos al formulario seguro
    return redirect('confirmar_cambios_perfil')

@login_required(login_url='login')
def confirmar_cambios_perfil(request):
    usuario = request.user

    if request.method == 'POST':
        # Recogemos los datos del formulario
        codigo_ingresado = request.POST.get('codigo')
        nuevo_username = request.POST.get('username')
        nuevo_email = request.POST.get('email')
        nueva_pass = request.POST.get('password')
        
        # 1. VERIFICAMOS EL CÓDIGO
        codigo_real = request.session.get('codigo_seguridad')
        
        if not codigo_real or codigo_ingresado != codigo_real:
            return render(request, 'usuarios/editar_perfil_seguro.html', {
                'error': 'El código de seguridad es incorrecto o ha caducado.',
                'usuario': usuario
            })
            
        # 2. SI EL CÓDIGO ES CORRECTO, APLICAMOS CAMBIOS
        cambios_realizados = []
        
        if nuevo_username and nuevo_username != usuario.username:
            usuario.username = nuevo_username
            cambios_realizados.append("Usuario")
            
        if nuevo_email and nuevo_email != usuario.email:
            usuario.email = nuevo_email
            cambios_realizados.append("Email")
            
        if nueva_pass:
            usuario.set_password(nueva_pass) # Encriptamos la nueva pass
            cambios_realizados.append("Contraseña")

        usuario.save()
        
        # Si cambió la contraseña, hay que mantener la sesión activa
        if nueva_pass:
            update_session_auth_hash(request, usuario)

        # Borramos el código de la sesión por seguridad
        del request.session['codigo_seguridad']
        
        return render(request, 'usuarios/perfil.html', {
            'usuario': usuario,
            'mensaje_exito': f"¡Datos actualizados correctamente! ({', '.join(cambios_realizados)})"
        })

    return render(request, 'usuarios/editar_perfil_seguro.html', {'usuario': usuario})