import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from .models import Viatura, HistoricoManutencao, AberturaTurnoViatura, Motorista

@login_required
def dashboard(request):
    viaturas = Viatura.objects.all().order_by('prefixo')
    
    # Calculate resumo statistics
    autos_qs = viaturas.exclude(tipo=Viatura.TipoViatura.MOTO)
    motos_qs = viaturas.filter(tipo=Viatura.TipoViatura.MOTO)
    
    # Autos stats
    autos_em_300 = autos_qs.filter(status__in=[Viatura.StatusViatura.OPERANDO, 'operante']).count()
    autos_vai_baixar = autos_qs.filter(status__in=[Viatura.StatusViatura.VAI_BAIXAR, 'baixada_rodando']).count()
    autos_baixada_batalhao = autos_qs.filter(status=Viatura.StatusViatura.BAIXADA_BATALHAO).count()
    autos_baixada_oficina = autos_qs.filter(status__in=[Viatura.StatusViatura.BAIXADA_OFICINA, 'baixada']).count()
    autos_total = autos_qs.count()
    
    # Motos stats
    motos_em_300 = motos_qs.filter(status__in=[Viatura.StatusViatura.OPERANDO, 'operante']).count()
    motos_vai_baixar = motos_qs.filter(status__in=[Viatura.StatusViatura.VAI_BAIXAR, 'baixada_rodando']).count()
    motos_baixada_batalhao = motos_qs.filter(status=Viatura.StatusViatura.BAIXADA_BATALHAO).count()
    motos_baixada_oficina = motos_qs.filter(status__in=[Viatura.StatusViatura.BAIXADA_OFICINA, 'baixada']).count()
    motos_total = motos_qs.count()
    
    resumo = {
        'autos': {
            'em_300': autos_em_300,
            'vai_baixar': autos_vai_baixar,
            'baixada_batalhao': autos_baixada_batalhao,
            'baixada_oficina': autos_baixada_oficina,
            'total': autos_total,
        },
        'motos': {
            'em_300': motos_em_300,
            'vai_baixar': motos_vai_baixar,
            'baixada_batalhao': motos_baixada_batalhao,
            'baixada_oficina': motos_baixada_oficina,
            'total': motos_total,
        },
        'total_geral': viaturas.count()
    }
    
    return render(request, 'frota/dashboard.html', {
        'viaturas': viaturas,
        'resumo': resumo
    })

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
        status = data.get('status', 'operando')
        
        if not prefixo or not placa or not modelo:
            return JsonResponse({'error': 'Preencha prefixo, placa e modelo.'}, status=400)

        if viatura_id:
            # Edit
            v = get_object_or_404(Viatura, pk=viatura_id)
            if km_atual != v.km_atual and v.has_open_turno:
                return JsonResponse({'error': 'Não é possível alterar a quilometragem atual do veículo pois há um turno aberto para ele.'}, status=400)
            v.prefixo = prefixo
            v.placa = placa
            v.marca = marca
            v.modelo = modelo
            v.tipo = tipo
            v.km_atual = km_atual
            v.limite_troca_oleo = limite_troca_oleo
            v.status = status
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
                limite_troca_oleo=limite_troca_oleo,
                status=status
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
        if v.status in [Viatura.StatusViatura.BAIXADA_OFICINA, Viatura.StatusViatura.BAIXADA_BATALHAO, 'baixada']:
            return JsonResponse({'error': 'A viatura já está baixada.'}, status=400)

        # Atualizar viatura
        v.status = Viatura.StatusViatura.BAIXADA_OFICINA
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
        if v.status not in [Viatura.StatusViatura.BAIXADA_OFICINA, Viatura.StatusViatura.BAIXADA_BATALHAO, 'baixada']:
            return JsonResponse({'error': 'A viatura não está baixada.'}, status=400)

        # Atualizar histórico em aberto
        historico = v.manutencoes.filter(concluida=False).last()
        if historico:
            historico.concluida = True
            historico.data_retorno = timezone.now()
            historico.save()

        # Atualizar viatura
        v.status = Viatura.StatusViatura.OPERANDO
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

@login_required
def abertura_turno_view(request):
    return render(request, 'frota/abertura_turno.html')

@login_required
@require_GET
def api_viaturas_operantes(request):
    try:
        viaturas_ativas = Viatura.objects.filter(
            status__in=[
                Viatura.StatusViatura.OPERANDO,
                Viatura.StatusViatura.VAI_BAIXAR,
                'operante',
                'baixada_rodando'
            ]
        ).order_by('prefixo')
        aberturas = AberturaTurnoViatura.objects.filter(data_encerramento__isnull=True)
        
        abertura_dict = {a.viatura_id: a for a in aberturas}
        
        dados = []
        for v in viaturas_ativas:
            abertura = abertura_dict.get(v.id)
            if abertura:
                km = abertura.km_inicial
                selecionado = True
                motorista_nome = abertura.motorista.nome if abertura.motorista else ''
            else:
                km = v.km_atual
                selecionado = False
                motorista_nome = ''
                
            dados.append({
                'id': v.id,
                'prefixo': v.prefixo,
                'placa': v.placa,
                'modelo': v.modelo,
                'km_atual': km,
                'selecionado': selecionado,
                'motorista': motorista_nome
            })
            
        return JsonResponse({'viaturas': dados})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

from django.db import transaction

@login_required
@require_POST
def api_salvar_abertura_turno(request):
    try:
        import re
        payload = json.loads(request.body)
        viaturas_dados = payload.get('viaturas', [])
        
        with transaction.atomic():
            for v_data in viaturas_dados:
                v_id = v_data.get('id')
                km_inicial = int(v_data.get('km_inicial', 0))
                motorista_raw = v_data.get('motorista', '').strip()
                
                v = Viatura.objects.get(pk=v_id)
                open_turno = v.turnos_abertos.filter(data_encerramento__isnull=True).first()
                
                if motorista_raw:
                    # Sanitize: letters and space only, uppercase
                    nome_limpo = re.sub(r'[^A-Z\s]', '', motorista_raw.upper()).strip()
                    if nome_limpo:
                        motorista_obj, _ = Motorista.objects.get_or_create(nome=nome_limpo)
                        
                        if open_turno:
                            open_turno.km_inicial = km_inicial
                            open_turno.motorista = motorista_obj
                            open_turno.save()
                        else:
                            open_turno = AberturaTurnoViatura.objects.create(
                                viatura=v,
                                km_inicial=km_inicial,
                                usuario=request.user,
                                data_abertura=timezone.now(),
                                motorista=motorista_obj
                            )
                        v.km_atual = km_inicial
                        v.save()
                    else:
                        if open_turno:
                            open_turno.delete()
                else:
                    if open_turno:
                        open_turno.delete()
                    
        return JsonResponse({'status': 'sucesso', 'message': 'Turno aberto/atualizado com sucesso.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_GET
def api_motoristas(request):
    try:
        motoristas = Motorista.objects.all().order_by('nome')
        dados = [m.nome for m in motoristas]
        return JsonResponse({'motoristas': dados})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def api_cancelar_abertura_turno(request):
    try:
        payload = json.loads(request.body)
        viatura_id = payload.get('viatura_id')
        v = get_object_or_404(Viatura, pk=viatura_id)
        
        open_turno = v.turnos_abertos.filter(data_encerramento__isnull=True).first()
        if open_turno:
            open_turno.delete()
            
        return JsonResponse({'status': 'sucesso', 'message': 'Abertura de turno cancelada com sucesso.', 'km_atual': v.km_atual})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
