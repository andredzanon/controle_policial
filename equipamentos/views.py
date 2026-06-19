import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Equipamento

@login_required
def dashboard(request):
    equipamentos = Equipamento.objects.all().order_by('nome')
    return render(request, 'equipamentos/dashboard.html', {'equipamentos': equipamentos})

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
