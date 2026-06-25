import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from datetime import datetime
from frota.models import Viatura, AberturaTurnoViatura
from .models import (
    RelatorioTurno, VeiculoAbordado, PessoaAbordada, VeiculoRecolhido,
    TesteEtilometrico, PrisaoApreensao, ApreensaoDroga
)

@login_required
def index(request):
    edit_id = request.GET.get('edit', '')
    return render(request, 'ocorrencias/index.html', {'edit_id': edit_id})

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

        # Veículos Recolhidos
        veiculos_recolhidos = data.get('veiculos_recolhidos', [])
        if veiculos_recolhidos:
            total_rec = sum(int(item[1]) for item in veiculos_recolhidos)
            linhas.append(f"*VEÍCULOS RECOLHIDOS: {total_rec}*")
            for item in veiculos_recolhidos:
                linhas.append(f"- {item[1]} {item[0]} ({item[2]})")
            linhas.append("")

        # Veículos Recuperados
        veiculos_recuperados = data.get('veiculos_recuperados', [])
        if veiculos_recuperados:
            total_recup = sum(int(item[1]) for item in veiculos_recuperados)
            linhas.append(f"*VEÍCULOS RECUPERADOS: {total_recup}*")
            for item in veiculos_recuperados:
                linhas.append(f"- {item[1]} {item[0]} ({item[2]})")
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
            turno_id = data.get('id')
            if turno_id:
                turno = RelatorioTurno.objects.get(pk=turno_id)
                turno.data = data_str
                turno.viatura = viatura
                turno.comandante = comandante
                turno.observacoes = data.get('observacoes', '')
                turno.dinheiro_apreendido = data.get('dinheiro_apreendido', 0)
                turno.save()
                
                # Excluir vínculos antigos
                turno.veiculos_abordados.all().delete()
                turno.pessoas_abordadas.all().delete()
                if hasattr(turno, 'teste_etilometrico'):
                    turno.teste_etilometrico.delete()
                turno.prisoes_apreensoes.all().delete()
                turno.drogas_apreendidas.all().delete()
                turno.veiculos_recolhidos.all().delete()
            else:
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
                if realizados > 0 or recusas > 0:
                    TesteEtilometrico.objects.create(turno=turno, realizados=realizados, recusas=recusas)

            # Salvar prisoes
            for p in data.get('prisoes', []):
                sexo = 'masculino' if p[0] == 'M' else 'feminino'
                PrisaoApreensao.objects.create(turno=turno, sexo=sexo, idade=int(p[1]))
                
            # Salvar drogas
            for d in data.get('drogas', []):
                ApreensaoDroga.objects.create(turno=turno, tipo=d[0], quantidade=float(d[1]), medida=d[2])

            # Salvar veículos recolhidos
            for vr in data.get('veiculos_recolhidos', []):
                destino = 'patio' if 'pátio' in vr[2].lower() else 'delegacia'
                VeiculoRecolhido.objects.create(turno=turno, tipo=vr[0], quantidade=int(vr[1]), destino=destino)

            # Salvar veículos recuperados
            for vr in data.get('veiculos_recuperados', []):
                destino = 'recuperado_patio' if 'pátio' in vr[2].lower() else 'recuperado_delegacia'
                VeiculoRecolhido.objects.create(turno=turno, tipo=vr[0], quantidade=int(vr[1]), destino=destino)

            km_final = data.get('km_final')
            if km_final:
                try:
                    abertura = AberturaTurnoViatura.objects.get(data=data_str, viatura=viatura)
                    abertura.km_final = int(km_final)
                    abertura.save()
                    if int(km_final) > viatura.km_atual:
                        viatura.km_atual = int(km_final)
                        viatura.save()
                except AberturaTurnoViatura.DoesNotExist:
                    pass

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
                tipo_v = v.tipo.capitalize()
                if tipo_v.lower() in ['automóvel', 'automovel']:
                    tipo_str = "Automóvel" if v.quantidade == 1 else "Automóveis"
                elif tipo_v.lower() == 'caminhão':
                    tipo_str = "Caminhão" if v.quantidade == 1 else "Caminhões"
                elif tipo_v.lower() == 'ônibus':
                    tipo_str = "Ônibus"
                else:
                    tipo_str = tipo_v if v.quantidade == 1 else f"{tipo_v}s"
                linhas.append(f"- {v.quantidade} {tipo_str}")
            linhas.append("")

        # Pessoas
        pessoas = turno.pessoas_abordadas.all()
        if pessoas.exists():
            total = sum(p.quantidade for p in pessoas)
            linhas.append(f"*PESSOAS ABORDADAS: {total}*")
            for p in pessoas:
                tipo_str = p.get_tipo_display()
                if p.quantidade > 1:
                    if tipo_str.lower() == 'condutor':
                        tipo_str = "Condutores"
                    else:
                        tipo_str = f"{tipo_str}s"
                linhas.append(f"- {p.quantidade} {tipo_str}")
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

        # Veículos Recolhidos
        recolhidos = turno.veiculos_recolhidos.filter(destino__in=['patio', 'delegacia'])
        if recolhidos.exists():
            total = sum(r.quantidade for r in recolhidos)
            linhas.append(f"*VEÍCULOS RECOLHIDOS: {total}*")
            for r in recolhidos:
                destino_str = 'Pátio da CIA PM' if r.destino == 'patio' else 'Delegacia'
                linhas.append(f"- {r.quantidade} {r.tipo} ({destino_str})")
            linhas.append("")

        # Veículos Recuperados
        recuperados = turno.veiculos_recolhidos.filter(destino__in=['recuperado_patio', 'recuperado_delegacia', 'recuperado_outros'])
        if recuperados.exists():
            total = sum(r.quantidade for r in recuperados)
            linhas.append(f"*VEÍCULOS RECUPERADOS: {total}*")
            for r in recuperados:
                destino_str = 'Pátio da CIA PM' if r.destino == 'recuperado_patio' else ('Delegacia' if r.destino == 'recuperado_delegacia' else 'Outros')
                linhas.append(f"- {r.quantidade} {r.tipo} ({destino_str})")
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

from django.views.decorators.http import require_GET

@login_required
@require_GET
def api_viaturas_por_data(request):
    data_str = request.GET.get('data')
    if not data_str:
        return JsonResponse({'error': 'Data não fornecida.'}, status=400)
        
    aberturas = AberturaTurnoViatura.objects.filter(data=data_str).select_related('viatura')
    dados = []
    for a in aberturas:
        dados.append({
            'prefixo': a.viatura.prefixo,
            'modelo': a.viatura.modelo,
            'km_inicial': a.km_inicial
        })
        
    return JsonResponse({'viaturas': dados})

@login_required
def api_obter_dados_relatorio_json(request, pk):
    try:
        turno = RelatorioTurno.objects.get(pk=pk)
        
        km_inicial = ''
        km_final = ''
        try:
            abertura = AberturaTurnoViatura.objects.get(data=turno.data, viatura=turno.viatura)
            km_inicial = abertura.km_inicial
            km_final = abertura.km_final or ''
        except AberturaTurnoViatura.DoesNotExist:
            pass

        payload = {
            'id': turno.pk,
            'data': turno.data.strftime('%Y-%m-%d'),
            'viatura': turno.viatura.prefixo,
            'comandante': turno.comandante,
            'observacoes': turno.observacoes or '',
            'dinheiro_apreendido': float(turno.dinheiro_apreendido),
            'km_inicial': km_inicial,
            'km_final': km_final,
            'stats': {
                'veiculos_abordados': [],
                'pessoas_abordadas': [],
                'teste_etilometrico': []
            },
            'outros_veiculos': [],
            'prisoes': [],
            'drogas': [],
            'veiculos_recolhidos': [],
            'veiculos_recuperados': []
        }

        # Veículos Abordados
        for v in turno.veiculos_abordados.all():
            if v.tipo.lower() in ['automóvel', 'motocicleta']:
                label = f"{v.tipo}|{v.tipo}s" if v.tipo == 'Automóvel' else "Motocicleta|Motocicletas"
                payload['stats']['veiculos_abordados'].append({'valor': v.quantidade, 'label': label})
            else:
                payload['outros_veiculos'].append([v.tipo, v.quantidade])

        # Pessoas Abordadas
        for p in turno.pessoas_abordadas.all():
            tipo_cap = p.tipo.capitalize()
            label = f"{tipo_cap}|{tipo_cap}s"
            if p.tipo == 'transeunte':
                label = "Transeunte|Transeuntes"
            payload['stats']['pessoas_abordadas'].append({'valor': p.quantidade, 'label': label})

        # Teste Etilométrico
        if hasattr(turno, 'teste_etilometrico'):
            te = turno.teste_etilometrico
            payload['stats']['teste_etilometrico'].append({'valor': te.realizados, 'label': 'Teste Realizado|Testes Realizados'})
            payload['stats']['teste_etilometrico'].append({'valor': te.recusas, 'label': 'Recusa|Recusas'})

        # Prisões
        for p in turno.prisoes_apreensoes.all():
            sexo_char = 'M' if p.sexo == 'masculino' else 'F'
            payload['prisoes'].append([sexo_char, str(p.idade)])

        # Drogas
        for d in turno.drogas_apreendidas.all():
            payload['drogas'].append([d.tipo, str(float(d.quantidade)), d.medida])

        # Veículos Recolhidos e Recuperados
        for vr in turno.veiculos_recolhidos.all():
            if vr.destino in ['patio', 'delegacia']:
                recolhimento_label = 'Pátio da CIA PM' if vr.destino == 'patio' else 'Delegacia'
                payload['veiculos_recolhidos'].append([vr.tipo, str(vr.quantidade), recolhimento_label])
            elif vr.destino in ['recuperado_patio', 'recuperado_delegacia']:
                recolhimento_label = 'Pátio da CIA PM' if vr.destino == 'recuperado_patio' else 'Delegacia'
                payload['veiculos_recuperados'].append([vr.tipo, str(vr.quantidade), recolhimento_label])

        return JsonResponse(payload)
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
            tipo_v = v['tipo'].capitalize()
            if tipo_v.lower() in ['automóvel', 'automovel']:
                tipo_str = "Automóvel" if v['total'] == 1 else "Automóveis"
            elif tipo_v.lower() == 'caminhão':
                tipo_str = "Caminhão" if v['total'] == 1 else "Caminhões"
            elif tipo_v.lower() == 'ônibus':
                tipo_str = "Ônibus"
            else:
                tipo_str = tipo_v if v['total'] == 1 else f"{tipo_v}s"
            linhas.append(f"- {v['total']} {tipo_str}")
        linhas.append("")

    # Pessoas Abordadas
    pessoas = PessoaAbordada.objects.filter(turno__in=turnos).values('tipo').annotate(total=Sum('quantidade')).order_by('-total')
    if pessoas:
        total = sum(p['total'] for p in pessoas)
        linhas.append(f"*PESSOAS ABORDADAS: {total}*")
        for p in pessoas:
            tipo_display = p['tipo'].capitalize()
            if p['total'] > 1:
                if tipo_display.lower() == 'condutor':
                    tipo_str = "Condutores"
                else:
                    tipo_str = f"{tipo_display}s"
            else:
                tipo_str = tipo_display
            linhas.append(f"- {p['total']} {tipo_str}")
        linhas.append("")

    # Veículos Recolhidos
    recolhidos = VeiculoRecolhido.objects.filter(turno__in=turnos, destino__in=['patio', 'delegacia']).values('tipo', 'destino').annotate(total=Sum('quantidade')).order_by('-total')
    if recolhidos:
        total = sum(r['total'] for r in recolhidos)
        linhas.append(f"*VEÍCULOS RECOLHIDOS: {total}*")
        for r in recolhidos:
            destino_str = 'Pátio da CIA PM' if r['destino'] == 'patio' else 'Delegacia'
            linhas.append(f"- {r['total']} {r['tipo']} ({destino_str})")
        linhas.append("")

    # Veículos Recuperados
    recuperados = VeiculoRecolhido.objects.filter(turno__in=turnos, destino__in=['recuperado_patio', 'recuperado_delegacia', 'recuperado_outros']).values('tipo', 'destino').annotate(total=Sum('quantidade')).order_by('-total')
    if recuperados:
        total = sum(r['total'] for r in recuperados)
        linhas.append(f"*VEÍCULOS RECUPERADOS: {total}*")
        for r in recuperados:
            destino_str = 'Pátio da CIA PM' if r['destino'] == 'recuperado_patio' else ('Delegacia' if r['destino'] == 'recuperado_delegacia' else 'Outros')
            linhas.append(f"- {r['total']} {r['tipo']} ({destino_str})")
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
            if p['total'] == 1:
                sexo_texto = "Masculino" if p['sexo'] == 'masculino' else "Feminino"
                linhas.append(f"- {p['total']} Indivíduo ({sexo_texto})")
            else:
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
