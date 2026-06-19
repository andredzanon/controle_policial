import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from .models import Viatura, HistoricoManutencao

@login_required
def dashboard(request):
    viaturas = Viatura.objects.all().order_by('prefixo')
    return render(request, 'frota/dashboard.html', {'viaturas': viaturas})

@login_required
@require_POST
def api_salvar_viatura(request):
    try:
        data = json.loads(request.body)
        viatura_id = data.get('id')
        prefixo = data.get('prefixo', '').upper()
        placa = data.get('placa', '').upper()
        marca = data.get('marca', 'Não Informada')
        modelo = data.get('modelo', '')
        tipo = data.get('tipo', 'carro')
        km_atual = int(data.get('km_atual', 0))
        limite_troca_oleo = int(data.get('limite_troca_oleo', 10000))
        
        if not prefixo or not placa or not modelo:
            return JsonResponse({'error': 'Preencha prefixo, placa e modelo.'}, status=400)

        if viatura_id:
            # Edit
            v = get_object_or_404(Viatura, pk=viatura_id)
            v.prefixo = prefixo
            v.placa = placa
            v.marca = marca
            v.modelo = modelo
            v.tipo = tipo
            v.km_atual = km_atual
            v.limite_troca_oleo = limite_troca_oleo
            v.save()
            msg = 'Viatura atualizada com sucesso.'
        else:
            # Create
            v = Viatura.objects.create(
                prefixo=prefixo,
                placa=placa,
                marca=marca,
                modelo=modelo,
                tipo=tipo,
                km_atual=km_atual,
                limite_troca_oleo=limite_troca_oleo
            )
            msg = 'Viatura cadastrada com sucesso.'

        return JsonResponse({'status': 'sucesso', 'message': msg})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def api_enviar_manutencao(request):
    try:
        data = json.loads(request.body)
        viatura_id = data.get('viatura_id')
        motivo = data.get('motivo')
        local = data.get('local')
        observacoes = data.get('observacoes', '')

        if not viatura_id or not motivo or not local:
            return JsonResponse({'error': 'Preencha todos os campos obrigatórios.'}, status=400)

        v = get_object_or_404(Viatura, pk=viatura_id)
        if v.status == Viatura.StatusViatura.BAIXADA:
            return JsonResponse({'error': 'A viatura já está baixada.'}, status=400)

        # Atualizar viatura
        v.status = Viatura.StatusViatura.BAIXADA
        v.motivo_baixa = motivo
        v.localizacao_atual = local
        v.save()

        # Criar histórico
        HistoricoManutencao.objects.create(
            viatura=v,
            motivo=motivo,
            local=local,
            observacoes=observacoes
        )

        return JsonResponse({'status': 'sucesso', 'message': 'Viatura enviada para manutenção.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def api_retornar_manutencao(request):
    try:
        data = json.loads(request.body)
        viatura_id = data.get('viatura_id')

        v = get_object_or_404(Viatura, pk=viatura_id)
        if v.status != Viatura.StatusViatura.BAIXADA:
            return JsonResponse({'error': 'A viatura não está baixada.'}, status=400)

        # Atualizar histórico em aberto
        historico = v.manutencoes.filter(concluida=False).last()
        if historico:
            historico.concluida = True
            historico.data_retorno = timezone.now()
            historico.save()

        # Atualizar viatura
        v.status = Viatura.StatusViatura.OPERANTE
        v.motivo_baixa = ''
        v.localizacao_atual = ''
        v.save()

        return JsonResponse({'status': 'sucesso', 'message': 'Viatura retornada à operação.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_GET
def api_historico_manutencao(request, viatura_id):
    v = get_object_or_404(Viatura, pk=viatura_id)
    historico = v.manutencoes.all().order_by('-data_saida')
    data = []
    for h in historico:
        data.append({
            'data_saida': h.data_saida.strftime('%d/%m/%Y %H:%M'),
            'motivo': h.motivo,
            'local': h.local,
            'data_retorno': h.data_retorno.strftime('%d/%m/%Y %H:%M') if h.data_retorno else 'Em andamento',
            'concluida': h.concluida,
            'observacoes': h.observacoes
        })
    return JsonResponse({'historico': data})
