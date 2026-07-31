from django.db import models

class Equipamento(models.Model):
    class StatusEquipamento(models.TextChoices):
        OPERANTE = 'operante', 'Operante'
        DEFEITO = 'defeito', 'Com Defeito'
        MANUTENCAO = 'manutencao', 'Em Manutenção'

    class TipoEquipamento(models.TextChoices):
        ARMA = 'arma', 'Armamento'
        MUNICAO = 'municao', 'Munição'
        CELULAR = 'celular', 'SADE Celular inst.'
        IMPRESSORA = 'impressora', 'Impressora'
        ETILOMETRO = 'etilometro', 'Etilometro'
        MALETA = 'maleta', 'Maleta'
        OUTROS = 'outros', 'Outros'

    numero_patrimonio = models.CharField(max_length=100, blank=True, null=True)
    nome = models.CharField(max_length=150)
    quantidade = models.IntegerField(default=1)
    tipo = models.CharField(
        max_length=20,
        choices=TipoEquipamento.choices,
        default=TipoEquipamento.ARMA
    )
    status = models.CharField(
        max_length=20,
        choices=StatusEquipamento.choices,
        default=StatusEquipamento.OPERANTE
    )
    motivo_defeito = models.TextField(blank=True, null=True)
    localizacao_atual = models.CharField(max_length=200, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.numero_patrimonio})"
