from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    class NivelAcesso(models.TextChoices):
        ADMIN_MASTER = 'admin_master', 'Admin Master'
        ADMINISTRADOR = 'administrador', 'Administrador'
        OPERADOR = 'operador', 'Operador'

    nivel = models.CharField(
        max_length=20,
        choices=NivelAcesso.choices,
        default=NivelAcesso.OPERADOR
    )

    def __str__(self):
        return f"{self.username} - {self.get_nivel_display()}"
