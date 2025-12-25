from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import VotacionForm
from django.contrib import messages
from django.db.models import Sum
from .models import Votacion, Opcion, Voto
from .forms import VotacionForm
from usuarios.models import Usuario


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
    
    # ... (Lógica de votación POST se queda igual) ...
    # Lógica para VOTAR
    if request.method == 'POST' and 'btn_votar' in request.POST:
        # ... (Tu código actual de votar) ...
        # (Copialo de tu código anterior o déjalo como está si no lo has borrado)
        pass 

    # --- CÁLCULOS ---
    opciones = votacion.opciones.all()
    total_votos = votacion.votos_totales.count()
    
    total_vecinos_query = Usuario.objects.filter(cooperativa=votacion.cooperativa, rol=Usuario.VECINO)
    total_vecinos_count = total_vecinos_query.count()
    abstencion_count = total_vecinos_count - total_votos
    
    datos_grafica = []
    nombres_opciones = []
    votos_opciones = []
    
    mapa_votos_nombres = {} 
    
    # VERIFICAMOS EL PERMISO DE LA COMUNIDAD
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
            
            # SOLO llenamos la lista de nombres si hay permiso
            if permiso_ver_detalles:
                votantes = Voto.objects.filter(votacion=votacion, opcion_elegida=op).select_related('usuario')
                # Obtenemos nombre real y piso
                nombres_lista = [f"{v.usuario.first_name} {v.usuario.last_name} ({v.usuario.numero_vivienda or '?'})" for v in votantes]
                mapa_votos_nombres[op.texto] = nombres_lista

    # Listas de participación
    lista_abstencion = []
    lista_participacion = []
    
    # SOLO llenamos si hay permiso
    if permiso_ver_detalles:
        ids_votaron = Voto.objects.filter(votacion=votacion).values_list('usuario_id', flat=True)
        
        vecinos_sin_voto = total_vecinos_query.exclude(id__in=ids_votaron)
        lista_abstencion = [f"{u.first_name} {u.last_name} ({u.numero_vivienda or '?'})" for u in vecinos_sin_voto]
        
        vecinos_con_voto = total_vecinos_query.filter(id__in=ids_votaron)
        lista_participacion = [f"{u.first_name} {u.last_name} ({u.numero_vivienda or '?'})" for u in vecinos_con_voto]

    return render(request, 'votaciones/detalle_votacion.html', {
        'votacion': votacion,
        'opciones': opciones,
        'datos_grafica': datos_grafica,
        'ya_voto': ya_voto, # Asegúrate de tener esta variable calculada arriba como antes
        'total_votos': total_votos,
        'total_vecinos': total_vecinos_count,
        'abstencion': abstencion_count,
        'nombres_js': nombres_opciones,
        'votos_js': votos_opciones,
        # JSONs (estarán vacíos si no hay permiso)
        'mapa_votos_json': json.dumps(mapa_votos_nombres),
        'lista_abstencion_json': json.dumps(lista_abstencion),
        'lista_participacion_json': json.dumps(lista_participacion),
        # Pasamos el permiso al template para ocultar textos
        'permiso_ver_detalles': permiso_ver_detalles 
    })