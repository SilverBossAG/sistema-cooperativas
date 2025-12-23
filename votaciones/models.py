from django.db import models
from usuarios.models import Usuario, Cooperativa # Importamos los modelos existentes

class Votacion(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título de la Votación")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(verbose_name="Fecha límite para votar")
    activa = models.BooleanField(default=True, verbose_name="¿Está activa?")
    
    # Vinculamos la votación a una cooperativa específica
    cooperativa = models.ForeignKey(Cooperativa, on_delete=models.CASCADE, related_name='votaciones')
    
    # Vinculamos al creador (normalmente el presidente)
    creada_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='votaciones_creadas')

    def __str__(self):
        return f"{self.titulo} - {self.cooperativa.nombre}"

class Opcion(models.Model):
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=100, verbose_name="Opción (ej: Sí, No, Abstención)")
    votos_cantidad = models.PositiveIntegerField(default=0, verbose_name="Contador de votos")

    def __str__(self):
        return f"{self.texto} (en {self.votacion.titulo})"

class Voto(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='votos_emitidos')
    votacion = models.ForeignKey(Votacion, on_delete=models.CASCADE, related_name='votos_totales')
    opcion_elegida = models.ForeignKey(Opcion, on_delete=models.CASCADE)
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Esto es CRUCIAL: Impide que un usuario vote dos veces en la misma votación
        unique_together = ('usuario', 'votacion')

    def __str__(self):
        return f"Voto de {self.usuario.username} en {self.votacion.titulo}"
