import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from .models import Equipamento

@login_required
def dashboard(request):
    armamentos = Equipamento.objects.filter(tipo__in=['arma', 'municao']).order_by('nome')
    outros = Equipamento.objects.exclude(tipo__in=['arma', 'municao']).order_by('tipo', 'nome')

    # Summary table: group armaments by name, count operante vs baixado
    armamentos_resumo = Equipamento.objects.filter(
        tipo__in=['arma', 'municao']
    ).values('nome').annotate(
        operante=Count('id', filter=Q(status='operante')),
        baixado=Count('id', filter=Q(status__in=['defeito', 'manutencao'])),
        total=Count('id')
    ).order_by('nome')

    # Summary table: group other equipment by tipo
    tipo_labels = dict(Equipamento.TipoEquipamento.choices)
    equipamentos_resumo_qs = Equipamento.objects.exclude(
        tipo__in=['arma', 'municao']
    ).values('tipo').annotate(
        operante=Count('id', filter=Q(status='operante')),
        baixado=Count('id', filter=Q(status__in=['defeito', 'manutencao'])),
        total=Count('id')
    ).order_by('tipo')
    # Attach human-readable label
    equipamentos_resumo = []
    for row in equipamentos_resumo_qs:
        row['tipo_display'] = tipo_labels.get(row['tipo'], row['tipo'])
        equipamentos_resumo.append(row)

    return render(request, 'equipamentos/dashboard.html', {
        'armamentos': armamentos,
        'outros': outros,
        'armamentos_resumo': armamentos_resumo,
        'equipamentos_resumo': equipamentos_resumo,
    })

@login_required
@require_POST
def api_salvar_equipamento(request):
    try:
        data = json.loads(request.body)
        e_id = data.get('id')
        patrimonio = data.get('numero_patrimonio', '').strip().upper()
        nome = data.get('nome', '').strip()
        tipo = data.get('tipo', 'arma')
        status = data.get('status', 'operante')
        localizacao = data.get('localizacao_atual', '').strip()
        observacoes = data.get('observacoes', '').strip()

        if not patrimonio or not nome:
            return JsonResponse({'error': 'Preencha Patrimônio e Nome.'}, status=400)

        if e_id:
            e = get_object_or_404(Equipamento, pk=e_id)
            if Equipamento.objects.filter(numero_patrimonio=patrimonio).exclude(pk=e_id).exists():
                return JsonResponse({'error': 'Número de Patrimônio já cadastrado.'}, status=400)
            
            e.numero_patrimonio = patrimonio
            e.nome = nome
            e.tipo = tipo
            e.status = status
            e.localizacao_atual = localizacao
            e.observacoes = observacoes
            e.save()
            msg = 'Equipamento atualizado com sucesso.'
        else:
            if Equipamento.objects.filter(numero_patrimonio=patrimonio).exists():
                return JsonResponse({'error': 'Número de Patrimônio já cadastrado.'}, status=400)

            e = Equipamento.objects.create(
                numero_patrimonio=patrimonio,
                nome=nome,
                tipo=tipo,
                status=status,
                localizacao_atual=localizacao,
                observacoes=observacoes
            )
            msg = 'Equipamento cadastrado com sucesso.'

        return JsonResponse({'status': 'sucesso', 'message': msg})
    except Exception as ex:
        return JsonResponse({'error': str(ex)}, status=500)

@login_required
@require_POST
def api_excluir_equipamento(request):
    try:
        data = json.loads(request.body)
        e_id = data.get('id')
        if not e_id:
            return JsonResponse({'error': 'ID não fornecido.'}, status=400)
        e = get_object_or_404(Equipamento, pk=e_id)
        e.delete()
        return JsonResponse({'status': 'sucesso', 'message': 'Equipamento excluído com sucesso.'})
    except Exception as ex:
        return JsonResponse({'error': str(ex)}, status=500)

