import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, F, Avg
from .models import ItemPorMolde, Molde, Maquina, Colaborador, Problema, SolicitacaoManutencao, AcaoManutencao
from .services import MoldeService, ColaboradorService, SolicitacaoService # Importamos os serviços que criamos
from django.views.decorators.csrf import csrf_protect
from django.db.models.functions import ExtractMonth, ExtractYear

# ==============================================================================
# 1. TELA DE DASHBOARD
# ==============================================================================
def dashboard_view(request):

    # ==========================================================================
    # LÓGICA DO NOVO FILTRO DE PERÍODO (PADRÃO: ÚLTIMOS 30 DIAS)
    # ==========================================================================
    data_fim_padrao = timezone.now()
    data_inicio_padrao = data_fim_padrao - timedelta(days=30)
    
    # Captura as datas vindas da URL (via método GET do formulário)
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    # Se existirem datas informadas pelo usuário, converte para objeto datetime
    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        # Torna o datetime consciente do fuso horário para evitar warnings do Django
        data_inicio = timezone.make_aware(data_inicio)
    else:
        data_inicio = data_inicio_padrao
        data_inicio_str = data_inicio.strftime('%Y-%m-%d')
        
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
        # Define o fim do dia (23:59:59) para abranger todas as OSs do último dia
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
        data_fim = timezone.make_aware(data_fim)
    else:
        data_fim = data_fim_padrao
        data_fim_str = data_fim.strftime('%Y-%m-%d')

    # Executa a contagem das Ordens de Serviço filtradas por data no banco
    total_abertas_periodo = SolicitacaoManutencao.objects.filter(
        data_abertura__range=[data_inicio, data_fim]
    ).exclude(
    status='Concluído'
    ).count()
        
    total_fechadas_periodo = SolicitacaoManutencao.objects.filter(
        data_fechamento__range=[data_inicio, data_fim],
        status='Concluído'
    ).count()



    # SE O USUÁRIO CLICOU EM "SALVAR" NO MODAL
    if request.method == 'POST':
        tipo_acao = request.POST.get('tipo_acao')
        
        if tipo_acao == 'nova_solicitacao':
            # 1. Puxa todos os dados do formulário HTML
            molde_id = request.POST.get('molde_id')

            os_aberta = SolicitacaoManutencao.objects.filter(
                molde_id=molde_id
            ).exclude(status='Concluído').exists()

            if os_aberta:
                # Dispara a notificação de erro que aparecerá no toast flutuante
                messages.error(request, '⚠️ Operação cancelada: Este molde já possui uma manutenção em andamento!')
                
                # Interrompe a execução e recarrega a página atual
                # Substitua 'ferramentaria:dashboard' pelo nome correto da sua url se for diferente
                return redirect(request.META.get('HTTP_REFERER', '/')) 
            # ================================================================


            maquina_id = request.POST.get('maquina_id')
            operador_id = request.POST.get('operador_id')
            # ordem_producao = request.POST.get('ordem_producao')
            # data_op = request.POST.get('data_op')
            ordem_manutencao = request.POST.get('ordem_manutencao') 
            parecer_producao = request.POST.get('parecer_producao')
            
            # .getlist() captura todos os quadradinhos (checkbox) marcados
            lista_problemas = request.POST.getlist('problemas_ids') 
            
            # 2. Chama o Service para salvar no banco
            SolicitacaoService.abrir_solicitacao(
                molde_id=molde_id,
                maquina_id=maquina_id,
                operador_id=operador_id,
                #ordem_producao=ordem_producao,
                ordem_manutencao=ordem_manutencao,
                parecer_producao=parecer_producao,
                lista_problemas_ids=lista_problemas
            )
            
            messages.success(request, "Solicitação registrada com sucesso!")
            return redirect('ferramentaria:dashboard')
        
        elif tipo_acao == 'registrar_manutencao':
            os_id = request.POST.get('os_id')
            responsavel_id = request.POST.get('responsavel_id')
            parecer_ferramentaria = request.POST.get('parecer_ferramentaria')
            novo_status = request.POST.get('novo_status') # "Em Manutenção" ou "Concluído"
            
            # Captura a lista de checkboxes marcados
            lista_acoes_ids = request.POST.getlist('acoes_realizadas_ids')
            
            # VALIDAÇÃO DE SEGURANÇA REQUISITADA:
            # Se o status for "Concluído" e a lista de ações estiver vazia, cancela a operação
            if novo_status == 'Concluído' and not lista_acoes_ids:
                messages.error(
                    request, 
                    f"Erro ao salvar OS nº {os_id}: Para alterar o status para 'Concluído', é obrigatório selecionar pelo menos uma Ação Realizada!"
                )
                return redirect('ferramentaria:dashboard') # Redireciona de volta sem salvar nada

            # Se passar na validação (ou se for "Em Manutenção", que permite lista vazia), chama o Service
            SolicitacaoService.registrar_manutencao(
                os_id=os_id,
                responsavel_id=responsavel_id,
                parecer_ferramentaria=parecer_ferramentaria,
                novo_status=novo_status,
                lista_acoes_ids=lista_acoes_ids
            )
            
            messages.success(request, f"Manutenção gravada! OS nº {os_id} atualizada para '{novo_status}'.")
            return redirect('ferramentaria:dashboard')


    # ======================================================
    # LÓGICA DE EXIBIÇÃO (GET) E FILTRO DO DASHBOARD
    # ======================================================
    
    # 1. Pega o molde selecionado na URL (ex: ?molde=2)
    molde_selecionado_id = request.GET.get('molde')
    molde_selecionado = None
    itens_molde = []
    
    # Listas para o Gráfico
    labels_problemas = []
    valores_problemas = []

    if molde_selecionado_id:
        molde_selecionado = Molde.objects.get(id=molde_selecionado_id)
        itens_molde = ItemPorMolde.objects.filter(molde=molde_selecionado)
        
        # Filtra as OS apenas desse molde
        solicitacoes_molde = SolicitacaoManutencao.objects.filter(molde=molde_selecionado)
        
        # Conta a frequência de cada problema nas OS desse molde
        contagem_problemas = Problema.objects.filter(
            solicitacaomanutencao__in=solicitacoes_molde
        ).annotate(total=Count('id')).order_by('-total')
        
        for p in contagem_problemas:
            labels_problemas.append(p.problema)
            valores_problemas.append(p.total)

    pendencias = SolicitacaoManutencao.objects.filter(status__in=['Aberto', 'Em Manutenção']).order_by('-data_abertura')
    
    context = {
        'pendencias': pendencias,
        'lista_moldes': Molde.objects.filter(status = "Ativo"),
        'moldes': Molde.objects.filter(status = "Ativo"),
        'lista_maquinas': Maquina.objects.filter(status = "Ativo"),
        'lista_operadores': Colaborador.objects.filter(status = "Ativo", funcao__iexact='Operador'),
        'lista_problemas': Problema.objects.all(),
        'lista_acoes_manutencao': AcaoManutencao.objects.all(),
        'lista_ferramenteiros': Colaborador.objects.filter(status='Ativo', funcao__iexact='Ferramenteiro'),
        
        # Variáveis novas enviadas para o HTML do gráfico
        'molde_selecionado_id': str(molde_selecionado_id) if molde_selecionado_id else None,
        'molde_selecionado': molde_selecionado,
        'itens_molde': itens_molde,
        'labels_problemas': json.dumps(labels_problemas),
        'valores_problemas': json.dumps(valores_problemas),
        'total_abertas_periodo': total_abertas_periodo,
        'total_fechadas_periodo': total_fechadas_periodo,
        'data_inicio_filtro': data_inicio_str,
        'data_fim_filtro': data_fim_str,
    }
    
    return render(request, 'ferramentaria/dashboard.html', context)

# ==============================================================================
# 2. TELA DE HISTÓRICO E REGISTROS 
# ==============================================================================
def historico_view(request):
    # 🟢 1. PROCESSA A GRAVAÇÃO SE O MODAL ENVIAR UM POST
    if request.method == 'POST':
        tipo_acao = request.POST.get('tipo_acao')
        if tipo_acao == 'registrar_manutencao':
            os_id = request.POST.get('os_id')
            responsavel_id = request.POST.get('responsavel_id')
            parecer_ferramentaria = request.POST.get('parecer_ferramentaria')
            novo_status = request.POST.get('novo_status')
            lista_acoes_ids = request.POST.getlist('acoes_realizadas_ids')
            
            # Validação idêntica à do Dashboard para segurança da ferramentaria
            if novo_status == 'Concluído' and not lista_acoes_ids:
                messages.error(
                    request, 
                    f"Erro ao salvar OS nº {os_id}: Para alterar o status para 'Concluído', é obrigatório selecionar pelo menos uma Ação Realizada!"
                )
                return redirect(request.get_full_path()) # Recarrega mantendo o molde filtrado na tela

            # Executa a atualização na base através do service existente
            SolicitacaoService.registrar_manutencao(
                os_id=os_id,
                responsavel_id=responsavel_id,
                parecer_ferramentaria=parecer_ferramentaria,
                novo_status=novo_status,
                lista_acoes_ids=lista_acoes_ids
            )
            
            #messages.success(request, f"Ficha nº {os_id} atualizada com sucesso!")
            return redirect(request.get_full_path()) # Recarrega na mesma página com os filtros preservados

    # 2. CAPTURA DOS FILTROS DA TELA (GET NORMAL)
    molde_id = request.GET.get('molde_filtro')
    lista_moldes = Molde.objects.filter(status="Ativo")
    
    solicitacoes = []
    molde_selecionado = None
    labels_defeitos_gerais = []
    valores_defeitos_gerais = []

    if molde_id and molde_id != 'todos':
        molde_selecionado = get_object_or_404(Molde, id=molde_id)
        # Traz histórico estruturado com prefetch_related reverso para otimizar velocidade
        solicitacoes = SolicitacaoManutencao.objects.filter(
            molde=molde_selecionado
        ).order_by('-id').prefetch_related('problemas', 'solicitacaoacao_set__acao')
        itens_molde = ItemPorMolde.objects.filter(molde=molde_selecionado)
        
        status_data = SolicitacaoManutencao.objects.filter(molde=molde_selecionado).values('status').annotate(total=Count('id'))
        top_data = Problema.objects.filter(solicitacaomanutencao__molde=molde_selecionado).annotate(total=Count('id')).order_by('-total')[:5]
        titulo_top = "Principais Defeitos Deste Molde"
        labels_top = [p.problema for p in top_data]
        valores_top = [p.total for p in top_data]

        # NOVO: Cálculo do MTTR (Tempo Médio de Reparo) por Mês para o Molde
        mttr_data = SolicitacaoManutencao.objects.filter(
            molde=molde_selecionado, 
            status='Concluído',
            data_fechamento__isnull=False
        ).annotate(
            mes=ExtractMonth('data_abertura'),
            ano=ExtractYear('data_abertura'),
            duracao=F('data_fechamento') - F('data_abertura')
        ).values('ano', 'mes').annotate(
            tempo_medio=Avg('duracao')
        ).order_by('ano', 'mes')
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
        # 🟢 NOVO: Cálculo do MTTR para Todos os Moldes
        mttr_data = SolicitacaoManutencao.objects.filter(
            status='Concluído',
            data_fechamento__isnull=False
        ).annotate(
            mes=ExtractMonth('data_abertura'),
            ano=ExtractYear('data_abertura'),
            duracao=F('data_fechamento') - F('data_abertura')
        ).values('ano', 'mes').annotate(
            tempo_medio=Avg('duracao')
        ).order_by('ano', 'mes')

    labels_status = [item['status'] for item in status_data]
    valores_status = [item['total'] for item in status_data]
    
    # 🟢 Preparar os dados do MTTR para o Chart.js
    meses_nomes = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    labels_mttr = []
    valores_mttr = []

    for item in mttr_data:
        # Pega a média de tempo (Timedelta) e converte para Horas totais (Float)
        if item['tempo_medio']:
            horas = item['tempo_medio'].total_seconds() / 3600.0
            labels_mttr.append(f"{meses_nomes[item['mes']]}/{str(item['ano'])[-2:]}")
            valores_mttr.append(round(horas, 1))

    context = {
        'solicitacoes': solicitacoes,
        'lista_moldes': lista_moldes,
        'molde_filtro': molde_id,
        'molde_selecionado': molde_selecionado,
        'labels_status': json.dumps(labels_status),
        'valores_status': json.dumps(valores_status),
        'labels_top': json.dumps(labels_top),
        'valores_top': json.dumps(valores_top),
        'titulo_top': titulo_top,
        'labels_defeitos_gerais': json.dumps(labels_defeitos_gerais),
        'valores_defeitos_gerais': json.dumps(valores_defeitos_gerais),
        'itens_molde': itens_molde,
        'lista_ferramenteiros': Colaborador.objects.filter(status='Ativo', funcao__iexact='Ferramenteiro'),
        'lista_acoes_manutencao': AcaoManutencao.objects.all().order_by('acao'),
        # 🟢 NOVAS SELEÇÕES ENVIADAS PARA ALIMENTAR NOVO GRAFICO
        'labels_mttr': json.dumps(labels_mttr),
        'valores_mttr': json.dumps(valores_mttr),
    }
    return render(request, 'ferramentaria/historico.html', context)
# ==============================================================================
# 3. TELA DE GERENCIAMENTO (CADASTRAR MOLDES, ETC)
# ==============================================================================


@csrf_protect # ISTO FORÇA O DJANGO A GERAR O TOKEN PARA ESTA TELA
def gerenciamento_view(request):
    context = {
        'colaboradores': Colaborador.objects.all().order_by('nome'),
        'maquinas': Maquina.objects.all().order_by('maquina'), # Ordenado pelo campo correto
        'acoes': AcaoManutencao.objects.all().order_by('acao'),
        'moldes': Molde.objects.all().order_by('molde_nome'), # Ordenado pelo campo correto
        'itens_molde': ItemPorMolde.objects.all().order_by('item_codigo'),
        'problemas': Problema.objects.all().order_by('problema'),
    }
    return render(request, 'ferramentaria/gerenciamento.html', context)

def salvar_molde(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id')
        molde_nome = request.POST.get('molde_nome', '').strip().upper()
        endereco_molde = request.POST.get('endereco_molde', '').strip().upper()
        status = request.POST.get('status', 'Ativo')
        
        duplicado = Molde.objects.filter(molde_nome__iexact=molde_nome)
        if id_reg:
            duplicado = duplicado.exclude(id=id_reg)
            
        if duplicado.exists():
            messages.error(request, f"Erro: O molde '{molde_nome}' já existe!")
            return redirect('/gerenciamento/?aba=aba-moldes')

        if id_reg: # Editar Existente
            obj = get_object_or_404(Molde, id=id_reg)
            obj.molde_nome = molde_nome
            obj.endereco_molde = endereco_molde # ADICIONADO
            obj.status = status                 # ADICIONADO
            obj.save()
            messages.success(request, "Molde atualizado com sucesso!")
        else: # Criar Novo
            # ADICIONADO OS CAMPOS NO CREATE:
            Molde.objects.create(
                molde_nome=molde_nome, 
                endereco_molde=endereco_molde, 
                status=status
            )
            messages.success(request, "Novo molde cadastrado com sucesso!")
            
    return redirect('/gerenciamento/?aba=aba-moldes') # Redireciona para a aba correta do gerenciamento

def salvar_maquina(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id')
        maquina = request.POST.get('maquina', '').strip().upper()
        grupo_maquina = request.POST.get('grupo_maquina', '').strip().upper()
        descricao = request.POST.get('descricao', '').strip()
        status = request.POST.get('status', 'Ativo')
        
        duplicado = Maquina.objects.filter(maquina__iexact=maquina)
        if id_reg:
            duplicado = duplicado.exclude(id_maquina=id_reg)
            
        if duplicado.exists():
            messages.error(request, f"Erro: A máquina '{maquina}' já existe!")
            return redirect('/gerenciamento/?aba=aba-maquinas')

        if id_reg:
            obj = get_object_or_404(Maquina, id_maquina=id_reg)
            obj.maquina = maquina
            obj.grupo_maquina = grupo_maquina # ADICIONADO
            obj.descricao = descricao         # ADICIONADO
            obj.status = status
            obj.save()
        else:
            # ID omitido propositalmente para o SQLite auto-incrementar
            Maquina.objects.create(
                maquina=maquina, 
                grupo_maquina=grupo_maquina, 
                descricao=descricao, 
                status=status
            )
            
        messages.success(request, "Máquina salva com sucesso!")
    return redirect('/gerenciamento/?aba=aba-maquinas')

def salvar_item_molde(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id')
        id_ref_molde = request.POST.get('id_referencia_molde') # Captura o ID vindo do <select>
        item_codigo = request.POST.get('item_codigo', '').strip().upper()
        descricao = request.POST.get('descricao', '').strip()
        cod_complementar = request.POST.get('cod_complementar', '').strip().upper()
        linha = request.POST.get('linha', '').strip()
        status = request.POST.get('status', 'Ativo')
        
        # Tratamento para permitir salvar vazio/nulo se o operador não selecionar um molde
        # Se vier uma string vazia do select, vira None (NULL no banco)
        id_molde_tratado = int(id_ref_molde) if id_ref_molde and id_ref_molde.isdigit() else None

        # Validação de Duplicidade baseada no id_item
        duplicado = ItemPorMolde.objects.filter(item_codigo__iexact=item_codigo)
        if id_reg:
            duplicado = duplicado.exclude(id_item=id_reg)
            
        if duplicado.exists():
            messages.error(request, f"Erro: O código de item '{item_codigo}' já existe!")
            return redirect('/gerenciamento/?aba=aba-itens-molde')

        if id_reg: # Fluxo de EDIÇÃO
            obj = get_object_or_404(ItemPorMolde, id_item=id_reg)
            obj.molde_id = id_molde_tratado  # Usa a propriedade correta do seu Model!
            obj.item_codigo = item_codigo
            obj.descricao = descricao
            obj.cod_complementar = cod_complementar
            obj.linha = linha
            obj.status = status
            obj.save()
            messages.success(request, "Item de molde atualizado com sucesso!")
            
        else: # Fluxo de NOVO CADASTRO
            ItemPorMolde.objects.create(
                molde_id=id_molde_tratado,    # Usa a propriedade correta do seu Model!
                item_codigo=item_codigo,
                descricao=descricao,
                cod_complementar=cod_complementar,
                linha=linha,
                status=status
            )
            messages.success(request, "Novo item cadastrado com sucesso!")
            
    return redirect('/gerenciamento/?aba=aba-itens-molde')

def salvar_colaborador(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id') # Oculto no HTML, vem preenchido apenas na edição
        nome = request.POST.get('nome')
        funcao = request.POST.get('funcao')
        status = request.POST.get('status', 'Ativo')
        
        if id_reg: # Se tem ID, atualiza o existente
            obj = get_object_or_404(Colaborador, id=id_reg)
            obj.nome = nome
            obj.funcao = funcao
            obj.status = status
            obj.save()
            messages.success(request, "Colaborador atualizado com sucesso!")
        else: # Se não tem ID, o SQLite gera o próximo automaticamente
            Colaborador.objects.create(nome=nome, funcao=funcao, status=status)
            messages.success(request, "Novo colaborador cadastrado com sucesso!")
            
    return redirect('/gerenciamento/?aba=aba-colaboradores') # Corrigido aqui!


def salvar_problema(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id')
        texto_problema = request.POST.get('problema')
        texto_descricao = request.POST.get('descricao', '').strip()
        
        if id_reg:
            obj = get_object_or_404(Problema, id=id_reg)
            obj.problema = texto_problema
            obj.descricao = texto_descricao
            obj.save()
            messages.success(request, "Problema atualizado com sucesso!")
        else:
            Problema.objects.create(
                problema=texto_problema, 
                descricao=texto_descricao     # Grava na coluna física descricao
            )
            messages.success(request, "Novo problema cadastrado com sucesso!")
            
    return redirect('/gerenciamento/?aba=aba-problemas')


def salvar_acao(request):
    if request.method == 'POST':
        id_reg = request.POST.get('id')
        acao = request.POST.get('acao')
        
        if id_reg:
            obj = get_object_or_404(AcaoManutencao, id=id_reg)
            obj.acao = acao
            obj.save()
            messages.success(request, "Ação técnica atualizada com sucesso!")
        else:
            AcaoManutencao.objects.create(acao=acao)
            messages.success(request, "Nova ação técnica cadastrada com sucesso!")
            
    return redirect('/gerenciamento/?aba=aba-acoes')

