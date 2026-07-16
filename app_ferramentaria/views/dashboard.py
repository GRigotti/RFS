import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.db import transaction

from ..models import ItemPorMolde, Molde, Maquina, Colaborador, Problema, AcaoManutencao, SolicitacaoManutencao
from ..services import SolicitacaoService, MoldeService

@never_cache
@login_required(login_url='ferramentaria:login')
def dashboard_view(request):
    data_fim_padrao = timezone.now()
    data_inicio_padrao = data_fim_padrao - timedelta(days=30)
    is_ferramenteiro_ou_admin = request.user.groups.filter(name__in=['Ferramenteiro', 'Admin']).exists()
    
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    if data_inicio_str:
        data_inicio = timezone.make_aware(datetime.strptime(data_inicio_str, '%Y-%m-%d'))
    else:
        data_inicio = data_inicio_padrao
        data_inicio_str = data_inicio.strftime('%Y-%m-%d')
        
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        data_fim = timezone.make_aware(data_fim)
    else:
        data_fim = data_fim_padrao
        data_fim_str = data_fim.strftime('%Y-%m-%d')

    total_abertas_periodo = SolicitacaoManutencao.objects.filter(data_abertura__range=[data_inicio, data_fim]).exclude(status='Concluído').count()
    total_fechadas_periodo = SolicitacaoManutencao.objects.filter(data_fechamento__range=[data_inicio, data_fim], status='Concluído').count()

    if request.method == 'POST':
        tipo_acao = request.POST.get('tipo_acao')

        if tipo_acao == 'nova_solicitacao':
            molde_id = request.POST.get('molde_id')
            if SolicitacaoManutencao.objects.filter(molde_id=molde_id).exclude(status='Concluído').exists():
                messages.error(request, '⚠️ Operação cancelada: Este molde já possui uma manutenção em andamento!')
                return redirect(request.META.get('HTTP_REFERER', '/')) 
            

            pecas_str = request.POST.get('pecas_produzidas', '0')
            try:
                pecas_produzidas = int(pecas_str) if pecas_str else 0
            except ValueError:
                pecas_produzidas = 0
            try:
                with transaction.atomic():
                    MoldeService.adicionar_ciclos_por_pecas(
                        molde_id=molde_id, 
                        pecas_produzidas=pecas_produzidas,
                        usuario_logado=request.user # 🟢 Passando o usuário para o Log
                    )

                    moldes_ciclo = Molde.objects.get(id=molde_id)

                    SolicitacaoService.abrir_solicitacao(
                        molde_id=molde_id, maquina_id=request.POST.get('maquina_id'),
                        operador_id=request.POST.get('operador_id'), ordem_manutencao=request.POST.get('ordem_manutencao'),
                        parecer_producao=request.POST.get('parecer_producao'), lista_problemas_ids=request.POST.getlist('problemas_ids'),
                        item_id=request.POST.get('inValor'), usuario_logado=request.user, ultima_contagem=pecas_produzidas,ciclo_momento=moldes_ciclo.ciclos
                    )
                messages.success(request, "Solicitação registrada com sucesso!")
            except Exception as e:
                # Opcional: Se algo der errado no banco, exibe mensagem e cancela a operação
                messages.error(request, f"Erro ao registrar solicitação: {str(e)}")
            url_origem = request.POST.get('url_origem')
            if url_origem:
                return redirect(url_origem)
            else:
                return redirect('ferramentaria:dashboard')
        
        elif tipo_acao == 'registrar_manutencao':
            if not is_ferramenteiro_ou_admin:
                return redirect('ferramentaria:dashboard')
            
            os_id = request.POST.get('os_id')
            novo_status = request.POST.get('novo_status')
            lista_acoes_ids = request.POST.getlist('acoes_realizadas_ids')
            
            if novo_status == 'Concluído' and not lista_acoes_ids:
                messages.error(request, f"Erro ao salvar OS nº {os_id}: Para alterar o status para 'Concluído', é obrigatório selecionar pelo menos uma Ação Realizada!")
                return redirect('ferramentaria:dashboard')

            previsao = request.POST.get('previsao_retorno') or None

            SolicitacaoService.registrar_manutencao(
                os_id=os_id, responsavel_id=request.POST.get('responsavel_id'),
                parecer_ferramentaria=request.POST.get('parecer_ferramentaria'), novo_status=novo_status,
                lista_acoes_ids=lista_acoes_ids, motivo=request.POST.get('motivo_manutencao'),
                previsao=previsao, usuario_logado=request.user
            )
            messages.success(request, f"Manutenção gravada! OS nº {os_id} atualizada para '{novo_status}'.")
            return redirect('ferramentaria:dashboard')

    molde_selecionado_id = request.GET.get('molde')
    molde_selecionado = None
    itens_molde = []
    labels_problemas, valores_problemas = [], []

    if molde_selecionado_id:
        molde_selecionado = Molde.objects.get(id=molde_selecionado_id)
        itens_molde = ItemPorMolde.objects.filter(molde=molde_selecionado)
        contagem_problemas = Problema.objects.filter(solicitacaomanutencao__molde=molde_selecionado).annotate(total=Count('id')).order_by('-total')
        for p in contagem_problemas:
            labels_problemas.append(p.problema)
            valores_problemas.append(p.total)

    pendencias = SolicitacaoManutencao.objects.filter(status__in=['Aberto', 'Em Manutenção']).order_by('-data_abertura')
    
    context = {
        'pendencias': pendencias, 'lista_moldes': Molde.objects.filter(status="Ativo"),
        'moldes': Molde.objects.filter(status="Ativo").order_by('molde_nome'), 'lista_maquinas': Maquina.objects.filter(status="Ativo"),
        'lista_operadores': Colaborador.objects.filter(status="Ativo", funcao__iexact='Operador'), 'lista_problemas': Problema.objects.all(),
        'lista_acoes_manutencao': AcaoManutencao.objects.all(), 'lista_ferramenteiros': Colaborador.objects.filter(status='Ativo', funcao__iexact='Ferramenteiro'),
        'molde_selecionado_id': str(molde_selecionado_id) if molde_selecionado_id else None, 'molde_selecionado': molde_selecionado,
        'itens_molde': itens_molde, 'labels_problemas': json.dumps(labels_problemas), 'valores_problemas': json.dumps(valores_problemas),
        'total_abertas_periodo': total_abertas_periodo, 'total_fechadas_periodo': total_fechadas_periodo,
        'data_inicio_filtro': data_inicio_str, 'data_fim_filtro': data_fim_str, 'pode_editar': is_ferramenteiro_ou_admin,
    }
    return render(request, 'ferramentaria/dashboard.html', context)

def carregar_itens_por_molde(request):
    molde_id = request.GET.get('molde_id')
    itens = ItemPorMolde.objects.filter(molde_id=molde_id).exclude(cod_complementar__isnull=True).exclude(cod_complementar__exact='')
    dados = [{'id': item.id_item, 'texto': f"{item.cod_complementar}"} for item in itens]
    return JsonResponse(dados, safe=False)