from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse  # <--- IMPORTANTE: Necesario para la API en vivo
import json

# --- IMPORTACIONES LIMPIAS ---
# 1. Modelos y Forms de ESTA carpeta (votaciones)
from .models import Votacion, Opcion, Voto
from .forms import VotacionForm

# 2. Modelos de la OTRA carpeta (usuarios)
from usuarios.models import Usuario
# -----------------------------

@login_required(login_url='login')
def listar_votaciones(request):
    # Mostramos todas (activas y cerradas) ordenadas por fecha
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
            # Validación de fecha futura
            if form.cleaned_data['fecha_fin'] <= timezone.now():
                messages.error(request, "La fecha de cierre debe ser en el futuro.")
                return render(request, 'votaciones/crear_votacion.html', {'form': form})

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
    
    # 1. LOGICA DE VOTO
    if request.method == 'POST' and 'btn_votar' in request.POST:
        if not votacion.activa:
            messages.error(request, "La votación ha finalizado.")
        elif ya_voto:
            messages.warning(request, "Ya has votado.")
        else:
            opcion_id = request.POST.get('opcion_seleccionada')
            if opcion_id:
                opcion = get_object_or_404(Opcion, id=opcion_id)
                Voto.objects.create(usuario=request.user, votacion=votacion, opcion_elegida=opcion)
                opcion.votos_cantidad += 1
                opcion.save()
                messages.success(request, "¡Tu voto ha sido registrado!")
                return redirect('ver_votacion', id_votacion=votacion.id)

    # 2. CÁLCULOS ESTÁNDAR
    opciones = votacion.opciones.all()
    total_votos = votacion.votos_totales.count()
    
    # Censo: todos menos superadmin
    total_censo = Usuario.objects.filter(
        cooperativa=votacion.cooperativa
    ).exclude(rol=Usuario.SUPERADMIN).count()
    
    abstencion = total_censo - total_votos
    
    datos_grafica = []
    nombres_opciones = []
    votos_opciones = []
    mapa_votos_nombres = {} 
    
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
                nombres = []
                for v in votantes:
                    nombre = f"{v.usuario.first_name} {v.usuario.last_name}"
                    if v.usuario == request.user:
                        nombre += " <strong>(MI VOTO)</strong>"
                    nombres.append(nombre)
                mapa_votos_nombres[op.texto] = nombres

    lista_abstencion = []
    lista_participacion = []
    
    if permiso_ver_detalles:
        ids_votaron = Voto.objects.filter(votacion=votacion).values_list('usuario_id', flat=True)
        base_usuarios = Usuario.objects.filter(cooperativa=votacion.cooperativa).exclude(rol=Usuario.SUPERADMIN)
        
        sin_voto = base_usuarios.exclude(id__in=ids_votaron)
        lista_abstencion = [f"{u.first_name} {u.last_name}" for u in sin_voto]
        
        con_voto = base_usuarios.filter(id__in=ids_votaron)
        for u in con_voto:
            texto = f"{u.first_name} {u.last_name}"
            if u == request.user:
                texto += " <strong>(YO)</strong>"
            lista_participacion.append(texto)

    return render(request, 'votaciones/detalle_votacion.html', {
        'votacion': votacion,
        'opciones': opciones,
        'datos_grafica': datos_grafica,
        'ya_voto': ya_voto,
        'total_votos': total_votos,
        'total_vecinos': total_censo,
        'abstencion': abstencion,
        'nombres_js': json.dumps(nombres_opciones),
        'votos_js': json.dumps(votos_opciones),
        'mapa_votos_json': json.dumps(mapa_votos_nombres),
        'lista_abstencion_json': json.dumps(lista_abstencion),
        'lista_participacion_json': json.dumps(lista_participacion),
        'permiso_ver_detalles': permiso_ver_detalles 
    })

# --- FUNCIÓN API PARA WEBSOCKETS ---
@login_required(login_url='login')
def datos_en_vivo(request, id_votacion):
    """
    Devuelve los datos en JSON cuando el WebSocket avisa de un cambio.
    """
    votacion = get_object_or_404(Votacion, id=id_votacion, cooperativa=request.user.cooperativa)
    
    # Recalculamos todo (copiado de la lógica principal para consistencia)
    activa = votacion.activa
    opciones = votacion.opciones.all()
    total_votos = votacion.votos_totales.count()
    
    total_censo = Usuario.objects.filter(
        cooperativa=votacion.cooperativa
    ).exclude(rol=Usuario.SUPERADMIN).count()
    
    abstencion = total_censo - total_votos
    
    nombres_opciones = []
    votos_opciones = []
    mapa_votos_nombres = {}
    
    permiso_ver_detalles = request.user.es_presidente and votacion.cooperativa.presidente_ve_votos
    
    for op in opciones:
        nombres_opciones.append(op.texto)
        votos_opciones.append(op.votos_cantidad)
        if permiso_ver_detalles:
            votantes = Voto.objects.filter(votacion=votacion, opcion_elegida=op).select_related('usuario')
            nombres = []
            for v in votantes:
                nombre = f"{v.usuario.first_name} {v.usuario.last_name}"
                if v.usuario == request.user:
                    nombre += " <strong>(MI VOTO)</strong>"
                nombres.append(nombre)
            mapa_votos_nombres[op.texto] = nombres

    lista_abstencion = []
    lista_participacion = []
    
    if permiso_ver_detalles:
        ids_votaron = Voto.objects.filter(votacion=votacion).values_list('usuario_id', flat=True)
        base_usuarios = Usuario.objects.filter(cooperativa=votacion.cooperativa).exclude(rol=Usuario.SUPERADMIN)
        
        sin_voto = base_usuarios.exclude(id__in=ids_votaron)
        lista_abstencion = [f"{u.first_name} {u.last_name}" for u in sin_voto]
        
        con_voto = base_usuarios.filter(id__in=ids_votaron)
        for u in con_voto:
            texto = f"{u.first_name} {u.last_name}"
            if u == request.user:
                texto += " <strong>(YO)</strong>"
            lista_participacion.append(texto)

    return JsonResponse({
        'activa': activa,
        'total_votos': total_votos,
        'abstencion': abstencion,
        'nombres_opciones': nombres_opciones,
        'votos_opciones': votos_opciones,
        'mapa_votos': mapa_votos_nombres,
        'lista_abstencion': lista_abstencion,
        'lista_participacion': lista_participacion
    })