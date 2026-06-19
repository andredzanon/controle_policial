# pyrefly: ignore [missing-import]
from django.db import models
from django.conf import settings
from frota.models import Viatura

class RelatorioTurno(models.Model):
    data = models.DateField()
    viatura = models.ForeignKey(Viatura, on_delete=models.PROTECT)
    comandante = models.CharField(max_length=150)
    observacoes = models.TextField(blank=True, null=True)
    dinheiro_apreendido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.data.strftime('%d/%m/%Y')} - {self.viatura.prefixo}"

class VeiculoAbordado(models.Model):
    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='veiculos_abordados')
    tipo = models.CharField(max_length=100) # Automóvel, Motocicleta, etc.
    quantidade = models.PositiveIntegerField(default=0)

class PessoaAbordada(models.Model):
    class TipoPessoa(models.TextChoices):
        CONDUTOR = 'condutor', 'Condutor'
        PASSAGEIRO = 'passageiro', 'Passageiro'
        TRANSEUNTE = 'transeunte', 'Transeunte'

    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='pessoas_abordadas')
    tipo = models.CharField(max_length=20, choices=TipoPessoa.choices)
    quantidade = models.PositiveIntegerField(default=0)

class VeiculoRecolhido(models.Model):
    class Destino(models.TextChoices):
        PATIO = 'patio', 'Pátio da Cia PM'
        DELEGACIA = 'delegacia', 'Delegacia'
        RECUPERADO_PATIO = 'recuperado_patio', 'Recuperado - Pátio'
        RECUPERADO_DELEGACIA = 'recuperado_delegacia', 'Recuperado - Delegacia'
        RECUPERADO_OUTROS = 'recuperado_outros', 'Recuperado - Outros'

    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='veiculos_recolhidos')
    tipo = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=0)
    destino = models.CharField(max_length=30, choices=Destino.choices)

class PrisaoApreensao(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = 'masculino', 'Masculino'
        FEMININO = 'feminino', 'Feminino'

    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='prisoes_apreensoes')
    sexo = models.CharField(max_length=15, choices=Sexo.choices)
    idade = models.PositiveIntegerField()

class ApreensaoDroga(models.Model):
    class Medida(models.TextChoices):
        GRAMA = 'g', 'g'
        QUILO = 'kg', 'kg'
        UNIDADE = 'und', 'und'
        MILILITRO = 'ml', 'ml'
        LITRO = 'L', 'L'

    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='drogas_apreendidas')
    tipo = models.CharField(max_length=100) # Maconha, Cocaína, etc.
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    medida = models.CharField(max_length=5, choices=Medida.choices)

class ObjetoApreendido(models.Model):
    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='objetos_apreendidos')
    descricao = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField(default=1)

class TesteEtilometrico(models.Model):
    turno = models.OneToOneField(RelatorioTurno, on_delete=models.CASCADE, related_name='teste_etilometrico')
    realizados = models.PositiveIntegerField(default=0)
    recusas = models.PositiveIntegerField(default=0)

class RegistroBOU(models.Model):
    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='registros_bou')
    ano_numero = models.CharField(max_length=20) # ex: 2024/001
    natureza = models.CharField(max_length=255)

class Notificacao(models.Model):
    class TipoNotificacao(models.TextChoices):
        PADRAO = 'padrao', 'Padrão'
        BLOQUEIO = 'bloqueio', 'Bloqueio'

    turno = models.ForeignKey(RelatorioTurno, on_delete=models.CASCADE, related_name='notificacoes')
    artigo = models.CharField(max_length=50) # ex: Art. 165
    quantidade = models.PositiveIntegerField(default=1)
    tipo = models.CharField(max_length=20, choices=TipoNotificacao.choices, default=TipoNotificacao.PADRAO)
