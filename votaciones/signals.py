# votaciones/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Voto, Votacion

@receiver(post_save, sender=Voto)
def avisar_nuevo_voto(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        grupo = f'votacion_{instance.votacion.id}'
        
        async_to_sync(channel_layer.group_send)(
            grupo,
            {
                'type': 'evento_actualizacion', # Llama al método del Consumer
            }
        )

@receiver(post_save, sender=Votacion)
def avisar_cambio_estado(sender, instance, **kwargs):
    # Avisar si el admin cierra la votación o cambia algo
    channel_layer = get_channel_layer()
    grupo = f'votacion_{instance.id}'
    
    async_to_sync(channel_layer.group_send)(
        grupo,
        {
            'type': 'evento_actualizacion',
        }
    )