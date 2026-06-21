import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from datetime import datetime
from frota.models import Viatura
from .models import (
    RelatorioTurno, VeiculoAbordado, PessoaAbordada, 
    TesteEtilometrico, PrisaoApreensao, ApreensaoDroga
)

@login_required
def index(request):
    viaturas = Viatura.objects.all().order_by('prefixo')
    return render(request, 'ocorrencias/index.html', {'viaturas': viaturas})

@login_required
@require_POST
def api_gerar_relatorio(request):
    try:
        data = json.loads(request.body)
        
        # Parse inputs
        data_str = data.get('data', '')
        viatura_str = data.get('viatura', '').upper()
        comandante = data.get('comandante', '').upper()
        
        if not data_str or not viatura_str or not comandante:
            return JsonResponse({'error': 'Preencha Data, Viatura e Comandante.'}, status=400)
            
        try:
            date_obj = datetime.strptime(data_str, '%Y-%m-%d')
            data_formatada = date_obj.strftime('%d/%m/%Y')
        except ValueError:
            data_formatada = data_str

        # Start building the report
        linhas = []
        linhas.append("*RELATÓRIO DE SERVIÇO*")
        linhas.append(f"Data: {data_formatada}")
        linhas.append(f"Viatura: {viatura_str}")
        linhas.append(f"Equipe: {comandante}")
        linhas.append("")

        dinheiro = data.get('dinheiro_apreendido', 0)
        if dinheiro and float(dinheiro) > 0:
            linhas.append(f"*DINHEIRO APREENDIDO:* R$ {float(dinheiro):.2f}".replace('.', ','))
            linhas.append("")

        stats = data.get('stats', {})
        categorias = {
            'veiculos_abordados': 'VEÍCULOS ABORDADOS',
            'pessoas_abordadas': 'PESSOAS ABORDADAS',
            'teste_etilometrico': 'TESTE ETILOMÉTRICO'
        }

        # Lógica no Back-end conforme RNF-20
        for cat_id, cat_nome in categorias.items():
            cat_data = stats.get(cat_id, [])
            
            # Incorpora "outros_veiculos" na listagem de veículos abordados
            if cat_id == 'veiculos_abordados':
                outros = data.get('outros_veiculos', [])
                for ov in outros:
                    cat_data.append({'valor': int(ov[1]), 'label': f"{ov[0]}|{ov[0]}"})

            if cat_data:
                total = sum(int(item['valor']) for item in cat_data)
                if total > 0:
                    linhas.append(f"*{cat_nome}: {total}*")
                    for item in cat_data:
                        labels = item['label'].split('|')
                        label_texto = labels[0] if int(item['valor']) == 1 else labels[1]
                        linhas.append(f"- {item['valor']} {label_texto}")
                    linhas.append("")

        # Dynamic lists
        prisoes = data.get('prisoes', [])
        if prisoes:
            linhas.append(f"*PRISÕES EFETUADAS: {len(prisoes)}*")
            for item in prisoes:
                sexo_texto = "Masc" if item[0] == 'M' else "Fem"
                linhas.append(f"- 1 Indivíduo ({sexo_texto}, {item[1]} anos)")
            linhas.append("")
            
        drogas = data.get('drogas', [])
        if drogas:
            linhas.append("*DROGAS APREENDIDAS:*")
            for item in drogas:
                linhas.append(f"- {item[1]}{item[2]} de {item[0]}")
            linhas.append("")

        obs = data.get('observacoes', '').strip()
        if obs:
            linhas.append("*OBSERVAÇÕES:*")
            linhas.append(obs)
            linhas.append("")

        texto_final = "\n".join(linhas).strip()

        return JsonResponse({'texto': texto_final})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def api_salvar_relatorio(request):
    try:
        data = json.loads(request.body)
        
        # Validations
        data_str = data.get('data')
        viatura_prefixo = data.get('viatura', '').upper()
        comandante = data.get('comandante', '').upper()
        
        if not data_str or not viatura_prefixo or not comandante:
            return JsonResponse({'error': 'Preencha os campos obrigatórios.'}, status=400)

        # Tratar a Viatura (Criar caso não exista para facilitar no MVP, 
        # embora o ideal seja pré-cadastrar)
        viatura, _ = Viatura.objects.get_or_create(
            prefixo=viatura_prefixo,
            defaults={'modelo': 'Não especificado', 'placa': viatura_prefixo}
        )

        with transaction.atomic():
            turno = RelatorioTurno.objects.create(
                data=data_str,
                viatura=viatura,
                comandante=comandante,
                observacoes=data.get('observacoes', ''),
                dinheiro_apreendido=data.get('dinheiro_apreendido', 0),
                created_by=request.user
            )

            stats = data.get('stats', {})
            
            # Salvar veículos abordados
            for item in stats.get('veiculos_abordados', []):
                tipo = item['label'].split('|')[0]
                VeiculoAbordado.objects.create(turno=turno, tipo=tipo, quantidade=item['valor'])
                
            # Salvar outros veículos
            for ov in data.get('outros_veiculos', []):
                VeiculoAbordado.objects.create(turno=turno, tipo=ov[0], quantidade=ov[1])
                
            # Salvar pessoas abordadas
            for item in stats.get('pessoas_abordadas', []):
                tipo = item['label'].split('|')[0].lower() # condutor, passageiro...
                PessoaAbordada.objects.create(turno=turno, tipo=tipo, quantidade=item['valor'])
                
            # Salvar teste etilométrico
            testes = stats.get('teste_etilometrico', [])
            if testes:
                realizados = sum(t['valor'] for t in testes if 'Realizado' in t['label'])
                recusas = sum(t['valor'] for t in testes if 'Recusa' in t['label'])
                TesteEtilometrico.objects.create(turno=turno, realizados=realizados, recusas=recusas)

            # Salvar prisoes
            for p in data.get('prisoes', []):
                sexo = 'masculino' if p[0] == 'M' else 'feminino'
                PrisaoApreensao.objects.create(turno=turno, sexo=sexo, idade=int(p[1]))
                
            # Salvar drogas
            for d in data.get('drogas', []):
                ApreensaoDroga.objects.create(turno=turno, tipo=d[0], quantidade=float(d[1]), medida=d[2])

        return JsonResponse({'status': 'sucesso', 'message': 'Relatório salvo com sucesso!'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def historico(request):
    data_filtro = request.GET.get('data', '')
    if data_filtro:
        turnos = RelatorioTurno.objects.filter(data=data_filtro).order_by('-created_at')
    else:
        turnos = RelatorioTurno.objects.all().order_by('-data', '-created_at')[:100] # Limite para não sobrecarregar
    
    return render(request, 'ocorrencias/historico.html', {
        'turnos': turnos,
        'data_filtro': data_filtro
    })

@login_required
@require_POST
def deletar_relatorio(request, pk):
    # RF-70: Apenas Admin_Master e Administrador podem excluir
    if request.user.nivel not in ['admin_master', 'administrador']:
        return JsonResponse({'error': 'Permissão negada. Apenas administradores podem excluir.'}, status=403)
        
    try:
        turno = RelatorioTurno.objects.get(pk=pk)
        turno.delete()
        return JsonResponse({'status': 'sucesso', 'message': 'Relatório excluído com sucesso.'})
    except RelatorioTurno.DoesNotExist:
        return JsonResponse({'error': 'Relatório não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_obter_texto_relatorio(request, pk):
    try:
        turno = RelatorioTurno.objects.get(pk=pk)
        
        linhas = []
        linhas.append("*RELATÓRIO DE SERVIÇO*")
        linhas.append(f"Data: {turno.data.strftime('%d/%m/%Y')}")
        linhas.append(f"Viatura: {turno.viatura.prefixo.upper()}")
        linhas.append(f"Equipe: {turno.comandante.upper()}")
        linhas.append("")

        if turno.dinheiro_apreendido > 0:
            linhas.append(f"*DINHEIRO APREENDIDO:* R$ {float(turno.dinheiro_apreendido):.2f}".replace('.', ','))
            linhas.append("")

        # Veículos
        veiculos = turno.veiculos_abordados.all()
        if veiculos.exists():
            total = sum(v.quantidade for v in veiculos)
            linhas.append(f"*VEÍCULOS ABORDADOS: {total}*")
            for v in veiculos:
                linhas.append(f"- {v.quantidade} {v.tipo.capitalize()}")
            linhas.append("")

        # Pessoas
        pessoas = turno.pessoas_abordadas.all()
        if pessoas.exists():
            total = sum(p.quantidade for p in pessoas)
            linhas.append(f"*PESSOAS ABORDADAS: {total}*")
            for p in pessoas:
                linhas.append(f"- {p.quantidade} {p.get_tipo_display()}")
            linhas.append("")

        # Etilométrico
        if hasattr(turno, 'teste_etilometrico'):
            te = turno.teste_etilometrico
            if te.realizados > 0 or te.recusas > 0:
                linhas.append(f"*TESTE ETILOMÉTRICO: {te.realizados + te.recusas}*")
                if te.realizados > 0: linhas.append(f"- {te.realizados} Realizados")
                if te.recusas > 0: linhas.append(f"- {te.recusas} Recusas")
                linhas.append("")

        # Prisões
        prisoes = turno.prisoes_apreensoes.all()
        if prisoes.exists():
            linhas.append(f"*PRISÕES EFETUADAS: {prisoes.count()}*")
            for p in prisoes:
                sexo_texto = "Masc" if p.sexo == 'masculino' else "Fem"
                linhas.append(f"- 1 Indivíduo ({sexo_texto}, {p.idade} anos)")
            linhas.append("")
            
        # Drogas
        drogas = turno.drogas_apreendidas.all()
        if drogas.exists():
            linhas.append("*DROGAS APREENDIDAS:*")
            for d in drogas:
                linhas.append(f"- {d.quantidade}{d.medida} de {d.tipo}")
            linhas.append("")

        if turno.observacoes:
            linhas.append("*OBSERVAÇÕES:*")
            linhas.append(turno.observacoes)
            linhas.append("")

        texto_final = "\n".join(linhas).strip()
        return JsonResponse({'texto': texto_final})

    except RelatorioTurno.DoesNotExist:
        return JsonResponse({'error': 'Relatório não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.db.models import Sum, Count

@login_required
def estatisticas_view(request):
    return render(request, 'ocorrencias/estatisticas.html')

@login_required
def api_estatisticas(request):
    tipo_filtro = request.GET.get('tipo', 'dia')
    
    if tipo_filtro == 'dia':
        data = request.GET.get('data')
        if not data:
            return JsonResponse({'error': 'Data não fornecida.'}, status=400)
        turnos = RelatorioTurno.objects.filter(data=data)
        periodo_texto = f"Data: {datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    else:
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        if not data_inicio or not data_fim:
            return JsonResponse({'error': 'Datas não fornecidas.'}, status=400)
        turnos = RelatorioTurno.objects.filter(data__range=[data_inicio, data_fim])
        periodo_texto = f"Período: {datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')} a {datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')}"

    if not turnos.exists():
        return JsonResponse({'texto': '*NENHUM REGISTRO ENCONTRADO NESSE PERÍODO*'})

    linhas = []
    linhas.append("*RELATÓRIO ESTATÍSTICO CONSOLIDADO*")
    linhas.append(periodo_texto)
    linhas.append(f"Total de Turnos/Viaturas: {turnos.count()}")
    linhas.append("")

    # Dinheiro
    total_dinheiro = turnos.aggregate(Sum('dinheiro_apreendido'))['dinheiro_apreendido__sum'] or 0
    if total_dinheiro > 0:
        linhas.append(f"*DINHEIRO APREENDIDO:* R$ {float(total_dinheiro):.2f}".replace('.', ','))
        linhas.append("")

    # Veículos Abordados
    veiculos = VeiculoAbordado.objects.filter(turno__in=turnos).values('tipo').annotate(total=Sum('quantidade')).order_by('-total')
    if veiculos:
        total = sum(v['total'] for v in veiculos)
        linhas.append(f"*VEÍCULOS ABORDADOS: {total}*")
        for v in veiculos:
            linhas.append(f"- {v['total']} {v['tipo'].capitalize()}")
        linhas.append("")

    # Pessoas Abordadas
    pessoas = PessoaAbordada.objects.filter(turno__in=turnos).values('tipo').annotate(total=Sum('quantidade')).order_by('-total')
    if pessoas:
        total = sum(p['total'] for p in pessoas)
        linhas.append(f"*PESSOAS ABORDADAS: {total}*")
        for p in pessoas:
            tipo_display = p['tipo'].capitalize()
            linhas.append(f"- {p['total']} {tipo_display}")
        linhas.append("")

    # Veículos Recolhidos
    from .models import VeiculoRecolhido
    recolhidos = VeiculoRecolhido.objects.filter(turno__in=turnos).values('tipo', 'destino').annotate(total=Sum('quantidade')).order_by('-total')
    if recolhidos:
        total = sum(r['total'] for r in recolhidos)
        linhas.append(f"*VEÍCULOS RECOLHIDOS/RECUPERADOS: {total}*")
        for r in recolhidos:
            linhas.append(f"- {r['total']} {r['tipo']} ({r['destino'].replace('_', ' ').title()})")
        linhas.append("")

    # Etilométrico
    testes = TesteEtilometrico.objects.filter(turno__in=turnos).aggregate(total_realizados=Sum('realizados'), total_recusas=Sum('recusas'))
    t_realizados = testes['total_realizados'] or 0
    t_recusas = testes['total_recusas'] or 0
    if t_realizados > 0 or t_recusas > 0:
        linhas.append(f"*TESTE ETILOMÉTRICO: {t_realizados + t_recusas}*")
        if t_realizados > 0: linhas.append(f"- {t_realizados} Realizados")
        if t_recusas > 0: linhas.append(f"- {t_recusas} Recusas")
        linhas.append("")

    # Prisões (Somente Quantidade por sexo)
    prisoes = PrisaoApreensao.objects.filter(turno__in=turnos).values('sexo').annotate(total=Count('id')).order_by('sexo')
    if prisoes:
        total = sum(p['total'] for p in prisoes)
        linhas.append(f"*PRISÕES EFETUADAS: {total}*")
        for p in prisoes:
            sexo_texto = "Masculinos" if p['sexo'] == 'masculino' else "Femininas"
            linhas.append(f"- {p['total']} Indivíduos ({sexo_texto})")
        linhas.append("")
        
    # Drogas
    drogas = ApreensaoDroga.objects.filter(turno__in=turnos).values('tipo', 'medida').annotate(total=Sum('quantidade')).order_by('tipo')
    if drogas:
        linhas.append("*DROGAS APREENDIDAS:*")
        for d in drogas:
            linhas.append(f"- {d['total']}{d['medida']} de {d['tipo']}")
        linhas.append("")

    # Objetos
    from .models import ObjetoApreendido
    objetos = ObjetoApreendido.objects.filter(turno__in=turnos).values('descricao').annotate(total=Sum('quantidade')).order_by('descricao')
    if objetos:
        total = sum(o['total'] for o in objetos)
        linhas.append(f"*OBJETOS APREENDIDOS: {total}*")
        for o in objetos:
            linhas.append(f"- {o['total']}x {o['descricao']}")
        linhas.append("")

    # Notificacoes
    from .models import Notificacao
    notificacoes = Notificacao.objects.filter(turno__in=turnos).values('artigo', 'tipo').annotate(total=Sum('quantidade')).order_by('-total')
    if notificacoes:
        total = sum(n['total'] for n in notificacoes)
        linhas.append(f"*NOTIFICAÇÕES DE TRÂNSITO: {total}*")
        for n in notificacoes:
            linhas.append(f"- {n['total']}x Art. {n['artigo']} ({n['tipo'].title()})")
        linhas.append("")

    # BOU (Apenas quantidade)
    from .models import RegistroBOU
    bous = RegistroBOU.objects.filter(turno__in=turnos).count()
    if bous > 0:
        linhas.append(f"*BOLETINS DE OCORRÊNCIA (BOU) FEITOS: {bous}*")
        linhas.append("")

    texto_final = "\n".join(linhas).strip()
    return JsonResponse({'texto': texto_final})
