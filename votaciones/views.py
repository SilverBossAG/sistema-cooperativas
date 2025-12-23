from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import VotacionForm
from django.contrib import messages
from django.db.models import Sum
from .models import Votacion, Opcion, Voto
from .forms import VotacionForm


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
        
        # Recogemos la lista de opciones del HTML (name="opciones")
        lista_opciones = request.POST.getlist('opciones')

        if form.is_valid():
            # 1. Validamos que haya al menos 2 opciones (opcional pero recomendable)
            # Filtramos las vacías por si acaso
            opciones_limpias = [op.strip() for op in lista_opciones if op.strip()]
            
            if len(opciones_limpias) < 2:
                messages.error(request, "Debes añadir al menos 2 opciones de respuesta.")
                return render(request, 'votaciones/crear_votacion.html', {'form': form})

            # 2. Guardamos la Votación
            nueva_votacion = form.save(commit=False)
            nueva_votacion.cooperativa = request.user.cooperativa
            nueva_votacion.creada_por = request.user
            nueva_votacion.save()

            # 3. Creamos las Opciones vinculadas
            for texto_opcion in opciones_limpias:
                Opcion.objects.create(
                    votacion=nueva_votacion,
                    texto=texto_opcion
                )

            messages.success(request, "Votación creada con sus opciones correctamente.")
            return redirect('listar_votaciones')
    else:
        form = VotacionForm()
    
    return render(request, 'votaciones/crear_votacion.html', {'form': form})

@login_required(login_url='login')
def ver_votacion(request, id_votacion):
    votacion = get_object_or_404(Votacion, id=id_votacion, cooperativa=request.user.cooperativa)
    
    # 1. Comprobamos si el usuario YA votó
    ya_voto = Voto.objects.filter(usuario=request.user, votacion=votacion).exists()
    
    # (EL BLOQUE 2 LO HEMOS BORRADO ENTERO)

    # 3. Lógica para VOTAR (Solo Vecinos que no han votado)
    if request.method == 'POST' and 'btn_votar' in request.POST:
        opcion_id = request.POST.get('opcion_seleccionada')
        if not ya_voto and opcion_id:
            opcion = get_object_or_404(Opcion, id=opcion_id)
            
            Voto.objects.create(
                usuario=request.user,
                votacion=votacion,
                opcion_elegida=opcion
            )
            
            opcion.votos_cantidad += 1
            opcion.save()
            
            messages.success(request, "¡Tu voto ha sido registrado!")
            return redirect('ver_votacion', id_votacion=votacion.id)

    # 4. Calcular porcentajes (Esto sigue igual)
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

    # Quitamos 'form_opcion' del contexto porque ya no existe
    return render(request, 'votaciones/detalle_votacion.html', {
        'votacion': votacion,
        'opciones': opciones,
        'datos_grafica': datos_grafica,
        'ya_voto': ya_voto,
        'total_votos': total_votos
    })