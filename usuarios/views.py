from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token # Necesario para Jinja2

def login_view(request):
    # CASO 1: El usuario ya rellenó el formulario y le dio a "Enviar" (POST)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Esto crea la sesión del usuario
            return redirect('panel_inicio') # Más tarde crearemos esta página
    
    # CASO 2: El usuario acaba de llegar a la página (GET)
    else:
        form = AuthenticationForm()

    # Le pasamos el 'csrf_token' manualmente para que Jinja2 no se queje
    context = {
        'form': form,
        'csrf_token': get_token(request), 
    }
    return render(request, 'login.html', context)

# Hacemos una vista simple para cerrar sesión también
def logout_view(request):
    logout(request)
    return redirect('login')

#funciones de inicio
@login_required(login_url='login') # Si no estás logueado, te manda al login
def panel_inicio(request):
    usuario = request.user
    
    # Preguntamos: ¿Qué rol tiene el usuario?
    if usuario.rol == usuario.SUPERADMIN:
        return render(request, 'dashboards/inicio_superadmin.html')
    
    elif usuario.rol == usuario.PRESIDENTE:
        return render(request, 'dashboards/inicio_presidente.html')
    
    else: # Si no es ninguno de los anteriores, es VECINO
        return render(request, 'dashboards/inicio_vecino.html')