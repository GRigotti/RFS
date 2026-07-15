import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, F, Avg
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models.functions import ExtractMonth, ExtractYear

from ..models import ItemPorMolde, Molde, Colaborador, Problema, SolicitacaoManutencao, AcaoManutencao
from ..services import SolicitacaoService

@never_cache
@login_required(login_url='ferramentaria:login')
def historico_view(request):
    is_ferramenteiro_ou_admin = request.user.groups.filter(name__in=['Ferramenteiro', 'Admin']).exists()
    
    if request.method == 'POST' and request.POST.get('tipo_acao') == 'registrar_manutencao':
        os_id = request.POST.get('os_id')
        novo_status = request.POST.get('novo_status')
        lista_acoes_ids = request.POST.getlist('acoes_realizadas_ids')
        
        if novo_status == 'Concluído' and not lista_acoes_ids:
            messages.error(request, f"Erro ao salvar OS nº {os_id}: Para alterar o status para 'Concluído', é obrigatório selecionar pelo menos uma Ação Realizada!")
            return redirect(request.get_full_path())

        previsao = request.POST.get('previsao_retorno') or None

        SolicitacaoService.registrar_manutencao(
            os_id=os_id, responsavel_id=request.POST.get('responsavel_id'),
            parecer_ferramentaria=request.POST.get('parecer_ferramentaria'), novo_status=novo_status,
            lista_acoes_ids=lista_acoes_ids, motivo=request.POST.get('motivo_manutencao'),
            previsao=previsao, usuario_logado=request.user
        )
        return redirect(request.get_full_path())

    molde_id = request.GET.get('molde')
    lista_moldes = Molde.objects.filter(status="Ativo").order_by('molde_nome')
    solicitacoes, labels_defeitos_gerais, valores_defeitos_gerais = [], [], []
    molde_selecionado = None

    if molde_id and molde_id != 'todos':
        molde_selecionado = get_object_or_404(Molde, id=molde_id)
        solicitacoes = SolicitacaoManutencao.objects.filter(molde=molde_selecionado).order_by('-id').prefetch_related('problemas', 'solicitacaoacao_set__acao')
        itens_molde = ItemPorMolde.objects.filter(molde=molde_selecionado)
        status_data = SolicitacaoManutencao.objects.filter(molde=molde_selecionado).values('status').annotate(total=Count('id'))
        top_data = Problema.objects.filter(solicitacaomanutencao__molde=molde_selecionado).annotate(total=Count('id')).order_by('-total')[:5]
        titulo_top = "Principais Defeitos Deste Molde"
        labels_top = [p.problema for p in top_data]
        valores_top = [p.total for p in top_data]

        mttr_data = SolicitacaoManutencao.objects.filter(molde=molde_selecionado, status='Concluído', data_fechamento__isnull=False).annotate(
            mes=ExtractMonth('data_abertura'), ano=ExtractYear('data_abertura'), duracao=F('data_fechamento') - F('data_abertura')
        ).values('ano', 'mes').annotate(tempo_medio=Avg('duracao')).order_by('ano', 'mes')
    else:
        molde_id = 'todos'
        itens_molde = []
        status_data = SolicitacaoManutencao.objects.values('status').annotate(total=Count('id'))
        top_data = Molde.objects.filter(solicitacaomanutencao__isnull=False).annotate(total=Count('solicitacaomanutencao')).order_by('-total')[:5]
        titulo_top = "Top 5 Moldes com Mais Ocorrências"
        labels_top = [m.molde_nome for m in top_data]
        valores_top = [m.total for m in top_data]
        
        defeitos_gerais_data = Problema.objects.filter(solicitacaomanutencao__isnull=False).annotate(total=Count('id')).order_by('-total')[:5]
        labels_defeitos_gerais = [p.problema for p in defeitos_gerais_data]
        valores_defeitos_gerais = [p.total for p in defeitos_gerais_data]

        mttr_data = SolicitacaoManutencao.objects.filter(status='Concluído', data_fechamento__isnull=False).annotate(
            mes=ExtractMonth('data_abertura'), ano=ExtractYear('data_abertura'), duracao=F('data_fechamento') - F('data_abertura')
        ).values('ano', 'mes').annotate(tempo_medio=Avg('duracao')).order_by('ano', 'mes')

    labels_status = [item['status'] for item in status_data]
    valores_status = [item['total'] for item in status_data]
    
    meses_nomes = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    labels_mttr, valores_mttr = [], []

    for item in mttr_data:
        if item['tempo_medio']:
            horas = item['tempo_medio'].total_seconds() / 3600.0
            labels_mttr.append(f"{meses_nomes[item['mes']]}/{str(item['ano'])[-2:]}")
            valores_mttr.append(round(horas, 1))

    context = {
        'solicitacoes': solicitacoes, 'lista_moldes': lista_moldes, 'molde_filtro': molde_id,
        'molde_selecionado': molde_selecionado, 'labels_status': json.dumps(labels_status), 'valores_status': json.dumps(valores_status),
        'labels_top': json.dumps(labels_top), 'valores_top': json.dumps(valores_top), 'titulo_top': titulo_top,
        'labels_defeitos_gerais': json.dumps(labels_defeitos_gerais), 'valores_defeitos_gerais': json.dumps(valores_defeitos_gerais),
        'itens_molde': itens_molde, 'lista_ferramenteiros': Colaborador.objects.filter(status='Ativo', funcao__iexact='Ferramenteiro'),
        'lista_acoes_manutencao': AcaoManutencao.objects.all().order_by('acao'), 'labels_mttr': json.dumps(labels_mttr),
        'valores_mttr': json.dumps(valores_mttr), 'pode_editar': is_ferramenteiro_ou_admin,'labels_defeitos_json': json.dumps(labels_top),    # Envia os defeitos do molde selecionado
        'valores_defeitos_json': json.dumps(valores_top),
    }
    return render(request, 'ferramentaria/historico.html', context)