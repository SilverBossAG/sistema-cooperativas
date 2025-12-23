from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import VotacionForm
from django.contrib import messages
from django.db.models import Sum
from .models import Votacion, Opcion, Voto
from .forms import VotacionForm, OpcionForm

@login_required(login_url='login')
def listar_votaciones(request):
    # Mostramos TODAS las votaciones de la cooperativa del usuario
    votaciones = Votacion.objects.filter(cooperativa=request.user.cooperativa).order_by('-fecha_creacion')
    
    return render(request, 'votaciones/listar_votaciones.html', {
        'votaciones': votaciones
    })

@login_required(login_url='login')
def crear_votacion(request):
    # Seguridad: Solo el presidente puede crear
    if not request.user.es_presidente:
        return redirect('listar_votaciones')
    
    if request.method == 'POST':
        form = VotacionForm(request.POST)
        if form.is_valid():
            nueva_votacion = form.save(commit=False)
            # Asignamos automáticamente la cooperativa y el autor
            nueva_votacion.cooperativa = request.user.cooperativa
            nueva_votacion.creada_por = request.user
            nueva_votacion.save()
            return redirect('listar_votaciones')
    else:
        form = VotacionForm()
    
    return render(request, 'votaciones/crear_votacion.html', {'form': form})

@login_required(login_url='login')
def ver_votacion(request, id_votacion):
    votacion = get_object_or_404(Votacion, id=id_votacion, cooperativa=request.user.cooperativa)
    
    # 1. Comprobamos si el usuario YA votó
    ya_voto = Voto.objects.filter(usuario=request.user, votacion=votacion).exists()
    
    # 2. Lógica para AÑADIR OPCIÓN (Solo Presidente)
    form_opcion = OpcionForm()
    if request.method == 'POST' and 'btn_add_opcion' in request.POST:
        if request.user.es_presidente:
            form_opcion = OpcionForm(request.POST)
            if form_opcion.is_valid():
                opcion = form_opcion.save(commit=False)
                opcion.votacion = votacion
                opcion.save()
                messages.success(request, "Opción añadida correctamente.")
                return redirect('ver_votacion', id_votacion=votacion.id)

    # 3. Lógica para VOTAR (Solo Vecinos que no han votado)
    if request.method == 'POST' and 'btn_votar' in request.POST:
        opcion_id = request.POST.get('opcion_seleccionada')
        if not ya_voto and opcion_id:
            opcion = get_object_or_404(Opcion, id=opcion_id)
            
            # Guardamos el voto
            Voto.objects.create(
                usuario=request.user,
                votacion=votacion,
                opcion_elegida=opcion
            )
            
            # Actualizamos el contador de la opción (para no tener que contar cada vez)
            opcion.votos_cantidad += 1
            opcion.save()
            
            messages.success(request, "¡Tu voto ha sido registrado!")
            return redirect('ver_votacion', id_votacion=votacion.id)

    # 4. Calcular porcentajes para la gráfica (Solo si ya votó o es admin)
    opciones = votacion.opciones.all()
    total_votos = votacion.votos_totales.count()
    
    datos_grafica = []
    if opciones:
        for op in opciones:
            porcentaje = (op.votos_cantidad / total_votos * 100) if total_votos > 0 else 0
            datos_grafica.append({
                'texto': op.texto,
                'votos': op.votos_cantidad,
                'porcentaje': round(porcentaje, 1)
            })

    return render(request, 'votaciones/detalle_votacion.html', {
        'votacion': votacion,
        'opciones': opciones, # Pasamos los datos calculados
        'datos_grafica': datos_grafica,
        'ya_voto': ya_voto,
        'form_opcion': form_opcion,
        'total_votos': total_votos
    })