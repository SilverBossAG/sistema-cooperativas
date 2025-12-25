from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. MODELO COOPERATIVA (El Edificio)
class Cooperativa(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Cooperativa")
    direccion = models.CharField(max_length=200, blank=True, verbose_name="Dirección")
    
    presidente_ve_votos = models.BooleanField(
        default=False, 
        verbose_name="¿El Presidente puede ver quién votó qué?"
    )

    class Meta:
        verbose_name = "Cooperativa"
        verbose_name_plural = "Cooperativas"

    def __str__(self):
        return self.nombre

# 2 TU USUARIO (Con Roles + Cooperativa)
class Usuario(AbstractUser):
    # --- TUS ROLES ---
    SUPERADMIN = 'SA'
    PRESIDENTE = 'PR'
    VECINO = 'VE'

    ROLES_CHOICES = [
        (SUPERADMIN, 'Super Admin'),
        (PRESIDENTE, 'Presidente Comunidad'),
        (VECINO, 'Vecino'),
    ]

    rol = models.CharField(
        max_length=2,
        choices=ROLES_CHOICES,
        default=VECINO,
        verbose_name="Rol en la comunidad"
    )
   
    numero_vivienda = models.CharField(
        max_length=10, 
        blank=True, 
        null=True, 
        verbose_name="Nº Vivienda/Piso"
    )

    # --- LA NUEVA VINCULACIÓN ---
    cooperativa = models.ForeignKey(
        Cooperativa, 
        on_delete=models.CASCADE, 
        related_name='usuarios',
        null=True, 
        blank=True,
        verbose_name="Cooperativa Asignada"
    )

    # Campo para obligar a cambiar la contraseña
    requiere_cambio_pass = models.BooleanField(default=True, verbose_name="Obligar cambio contraseña")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        coop = self.cooperativa.nombre if self.cooperativa else "Sin asignar"
        return f"{self.username} ({self.get_rol_display()}) - {coop}"

    # --- TUS ATAJOS ---
    @property
    def es_presidente(self):
        return self.rol == self.PRESIDENTE
    
    @property
    def es_vecino(self):
        return self.rol == self.VECINO