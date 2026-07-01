from django.db import models
from django.utils import timezone
from django.conf import settings

class Viatura(models.Model):
    class StatusViatura(models.TextChoices):
        OPERANDO = 'operando', 'Operando(300)'
        VAI_BAIXAR = 'vai_baixar', 'Vai Baixar'
        BAIXADA_BATALHAO = 'baixada_batalhao', 'Baixada(Batalhão)'
        BAIXADA_OFICINA = 'baixada_oficina', 'Baixada(Oficina)'

    class TipoViatura(models.TextChoices):
        CARRO = 'carro', 'Carro'
        MOTO = 'moto', 'Moto'
        FURGAO = 'furgao', 'Furgão'
        OUTROS = 'outros', 'Outros'

    prefixo = models.CharField(max_length=50, unique=True)
    placa = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50, default='Não Informada')
    modelo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TipoViatura.choices, default=TipoViatura.CARRO)
    status = models.CharField(
        max_length=20,
        choices=StatusViatura.choices,
        default=StatusViatura.OPERANDO
    )
    km_atual = models.IntegerField(default=0)
    limite_troca_oleo = models.IntegerField(default=10000, help_text="KM limite para a próxima troca de óleo")
    km_ultima_troca_oleo = models.IntegerField(default=0)
    motivo_baixa = models.TextField(blank=True, null=True)
    localizacao_atual = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.prefixo} - {self.modelo}"

    @property
    def has_open_turno(self):
        return self.turnos_abertos.filter(data_encerramento__isnull=True).exists()

    @property
    def open_turno(self):
        return self.turnos_abertos.filter(data_encerramento__isnull=True).first()

class HistoricoManutencao(models.Model):
    viatura = models.ForeignKey(Viatura, on_delete=models.CASCADE, related_name='manutencoes')
    data_saida = models.DateTimeField(default=timezone.now)
    motivo = models.TextField()
    local = models.CharField(max_length=200) # Oficina
    data_retorno = models.DateTimeField(null=True, blank=True)
    concluida = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.viatura.prefixo} - {self.data_saida.strftime('%d/%m/%Y')} a {'Ativa' if not self.concluida else self.data_retorno.strftime('%d/%m/%Y')}"

class RegistroQuilometragem(models.Model):
    viatura = models.ForeignKey(Viatura, on_delete=models.CASCADE, related_name='registros_km')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    km_inicial = models.IntegerField()
    km_final = models.IntegerField(null=True, blank=True)
    data_saida = models.DateTimeField(default=timezone.now)
    data_retorno = models.DateTimeField(null=True, blank=True)

class Motorista(models.Model):
    nome = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.nome

class AberturaTurnoViatura(models.Model):
    data = models.DateField(default=timezone.now)
    data_abertura = models.DateTimeField(default=timezone.now)
    data_encerramento = models.DateTimeField(null=True, blank=True)
    viatura = models.ForeignKey(Viatura, on_delete=models.CASCADE, related_name='turnos_abertos')
    km_inicial = models.IntegerField()
    km_final = models.IntegerField(null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    relatorio_turno = models.OneToOneField('ocorrencias.RelatorioTurno', on_delete=models.SET_NULL, null=True, blank=True, related_name='abertura_turno')
    motorista = models.ForeignKey(Motorista, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnos_abertos')

    def __str__(self):
        return f"{self.data_abertura.strftime('%d/%m/%Y %H:%M')} - {self.viatura.prefixo}"
