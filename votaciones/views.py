from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json  # <--- 1. IMPORTANTE: FALTABA ESTO

from .models import Votacion, Opcion, Voto
from .forms import VotacionForm
from usuarios.models import Usuario

@login_required(login_url='login')
def listar_votaciones(request):
    votaciones = Votacion.objects.filter(cooperativa=request.user.cooperativa).order_by('-fecha_creacion')
    return render(request, 'votaciones/listar_votaciones.html', {'votaciones': votaciones})

@login_required(login_url='login')
def crear_votacion(request):
    if not request.user.es_presidente:
        return redirect('listar_votaciones')
    
    if request.method == 'POST':
        form = VotacionForm(request.POST)
        lista_opciones = request.POST.getlist('opciones')

        if form.is_valid():
            opciones_limpias = [op.strip() for op in lista_opciones if op.strip()]
            if len(opciones_limpias) < 2:
                messages.error(request, "Debes añadir al menos 2 opciones.")
                return render(request, 'votaciones/crear_votacion.html', {'form': form})

            nueva_votacion = form.save(commit=False)
            nueva_votacion.cooperativa = request.user.cooperativa
            nueva_votacion.creada_por = request.user
            nueva_votacion.save()

            for texto_opcion in opciones_limpias:
                Opcion.objects.create(votacion=nueva_votacion, texto=texto_opcion)

            messages.success(request, "Votación creada correctamente.")
            return redirect('listar_votaciones')
    else:
        form = VotacionForm()
    return render(request, 'votaciones/crear_votacion.html', {'form': form})

@login_required(login_url='login')
def ver_votacion(request, id_votacion):
    votacion = get_object_or_404(Votacion, id=id_votacion, cooperativa=request.user.cooperativa)
    ya_voto = Voto.objects.filter(usuario=request.user, votacion=votacion).exists()
    
    # VOTAR
    if request.method == 'POST' and 'btn_votar' in request.POST:
        opcion_id = request.POST.get('opcion_seleccionada')
        if not ya_voto and opcion_id:
            opcion = get_object_or_404(Opcion, id=opcion_id)
            Voto.objects.create(usuario=request.user, votacion=votacion, opcion_elegida=opcion)
            opcion.votos_cantidad += 1
            opcion.save()
            messages.success(request, "¡Tu voto ha sido registrado!")
            return redirect('ver_votacion', id_votacion=votacion.id)

    # DATOS
    opciones = votacion.opciones.all()
    total_votos = votacion.votos_totales.count()
    
    total_vecinos = Usuario.objects.filter(cooperativa=votacion.cooperativa, rol=Usuario.VECINO).count()
    abstencion = total_vecinos - total_votos
    
    datos_grafica = []
    nombres_opciones = []
    votos_opciones = []
    mapa_votos_nombres = {} 
    
    # 2. SEGURIDAD (Esto estaba bien en tu archivo, lo mantenemos)
    permiso_ver_detalles = request.user.es_presidente and votacion.cooperativa.presidente_ve_votos

    if opciones:
        for op in opciones:
            porcentaje = (op.votos_cantidad / total_votos * 100) if total_votos > 0 else 0
            datos_grafica.append({
                'texto': op.texto,
                'votos': op.votos_cantidad,
                'porcentaje': round(porcentaje, 1)
            })
            nombres_opciones.append(op.texto)
            votos_opciones.append(op.votos_cantidad)
            
            if permiso_ver_detalles:
                votantes = Voto.objects.filter(votacion=votacion, opcion_elegida=op).select_related('usuario')
                # 3. Formateamos el nombre bonito
                nombres = [f"{v.usuario.first_name} {v.usuario.last_name}" for v in votantes]
                mapa_votos_nombres[op.texto] = nombres

    lista_abstencion = []
    lista_participacion = []
    
    if permiso_ver_detalles:
        ids_votaron = Voto.objects.filter(votacion=votacion).values_list('usuario_id', flat=True)
        vecinos_sin_voto = Usuario.objects.filter(cooperativa=votacion.cooperativa, rol=Usuario.VECINO).exclude(id__in=ids_votaron)
        lista_abstencion = [f"{u.first_name} {u.last_name}" for u in vecinos_sin_voto]
        
        vecinos_con_voto = Usuario.objects.filter(cooperativa=votacion.cooperativa, rol=Usuario.VECINO).filter(id__in=ids_votaron)
        lista_participacion = [f"{u.first_name} {u.last_name}" for u in vecinos_con_voto]

    return render(request, 'votaciones/detalle_votacion.html', {
        'votacion': votacion,
        'opciones': opciones,
        'datos_grafica': datos_grafica,
        'ya_voto': ya_voto,
        'total_votos': total_votos,
        'total_vecinos': total_vecinos,
        'abstencion': abstencion,
        # 4. LA SOLUCIÓN: Usar json.dumps
        'nombres_js': json.dumps(nombres_opciones),
        'votos_js': json.dumps(votos_opciones),
        'mapa_votos_json': json.dumps(mapa_votos_nombres),
        'lista_abstencion_json': json.dumps(lista_abstencion),
        'lista_participacion_json': json.dumps(lista_participacion),
        'permiso_ver_detalles': permiso_ver_detalles 
    })