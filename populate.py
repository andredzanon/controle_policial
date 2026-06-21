import random
from datetime import datetime, date
from django.contrib.auth import get_user_model
from frota.models import Viatura
from ocorrencias.models import (
    RelatorioTurno, VeiculoAbordado, PessoaAbordada, VeiculoRecolhido,
    PrisaoApreensao, ApreensaoDroga, ObjetoApreendido, TesteEtilometrico,
    RegistroBOU, Notificacao
)

Usuario = get_user_model()
user = Usuario.objects.first()
if not user:
    user = Usuario.objects.create_superuser('admin_test', 'admin@test.com', 'admin')

# Limpar dados antigos para ter um teste limpo (opcional, vou apenas adicionar)
# Mas vamos garantir que as viaturas não dupliquem
v1, _ = Viatura.objects.get_or_create(prefixo='VTR-001', defaults={'placa': 'ABC1234', 'modelo': 'Duster', 'status': 'operante'})
v2, _ = Viatura.objects.get_or_create(prefixo='VTR-002', defaults={'placa': 'DEF5678', 'modelo': 'Trailblazer', 'status': 'operante'})
moto, _ = Viatura.objects.get_or_create(prefixo='MOTO-01', defaults={'placa': 'XYZ9876', 'modelo': 'XRE 300', 'status': 'operante'})

viaturas = [v1, v2, moto]

datas_alvo = [
    ('2026-06-19', 2),
    ('2026-06-20', 2),
    ('2026-06-21', 1),
]

comandantes = ['SGT SILVA', 'CB OLIVEIRA', 'SD SANTOS']

for data_str, qtd in datas_alvo:
    for _ in range(qtd):
        turno = RelatorioTurno.objects.create(
            data=data_str,
            viatura=random.choice(viaturas),
            comandante=random.choice(comandantes),
            observacoes=f"Patrulhamento de rotina sem alterações graves.",
            dinheiro_apreendido=random.choice([0, 0, 50.00, 120.50]),
            created_by=user
        )

        # Veiculos
        VeiculoAbordado.objects.create(turno=turno, tipo='Automóvel', quantidade=random.randint(1, 5))
        VeiculoAbordado.objects.create(turno=turno, tipo='Motocicleta', quantidade=random.randint(0, 3))

        # Pessoas
        PessoaAbordada.objects.create(turno=turno, tipo='condutor', quantidade=random.randint(2, 6))
        PessoaAbordada.objects.create(turno=turno, tipo='passageiro', quantidade=random.randint(0, 4))

        # Teste Etilometrico
        TesteEtilometrico.objects.create(turno=turno, realizados=random.randint(0, 2), recusas=random.randint(0, 1))

        # Prisões (20% de chance)
        if random.random() < 0.2:
            PrisaoApreensao.objects.create(turno=turno, sexo='masculino', idade=random.randint(18, 45))

        # Drogas (20% de chance)
        if random.random() < 0.2:
            ApreensaoDroga.objects.create(turno=turno, tipo='Maconha', quantidade=random.randint(5, 50), medida='g')

        # BOUs
        for i in range(random.randint(0, 2)):
            RegistroBOU.objects.create(turno=turno, ano_numero=f"2026/{random.randint(1000, 9999)}", natureza="Averiguação")

print("Dados gerados com sucesso!")
