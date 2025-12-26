from django.db import models
from django.utils import timezone  # <--- IMPORTANTE PARA LA HORA
from usuarios.models import Usuario, Cooperativa

class Votacion(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título de la votación")
    descripcion = models.TextField(verbose_name="Descripción", blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Este es el campo clave para la hora exacta
    fecha_fin = models.DateTimeField(verbose_name="Fecha y hora de cierre")
    
    cooperativa = models.ForeignKey(Cooperativa, on_delete=models.CASCADE, related_name='votaciones')
    creada_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='votaciones_creadas')

    # Campo de resultados cacheados (opcional, pero útil)
    votos_totales = models.ManyToManyField(Usuario, through='Voto', related_name='votos_emitidos')

    # --- LA MAGIA: PROPIEDAD AUTOMÁTICA ---
    @property
    def activa(self):
        # Devuelve True si la hora actual es MENOR que la fecha de cierre
        return timezone.now() < self.fecha_fin

    def __str__(self):
        return self.titulo

class Opcion(models.Model):
    votacion = models.ForeignKey(Votacion, related_name='opciones', on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)
    votos_cantidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.texto

class Voto(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE)
    opcion_elegida = models.ForeignKey(Opcion, on_delete=models.CASCADE)
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'votacion')