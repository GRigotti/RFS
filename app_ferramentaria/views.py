import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from .models import ItemPorMolde, Molde, Maquina, Colaborador, Problema, SolicitacaoManutencao, AcaoManutencao
from .services import MoldeService, ColaboradorService, SolicitacaoService # Importamos os serviços que criamos

# ==============================================================================
# 1. TELA DE DASHBOARD
# ==============================================================================
def dashboard_view(request):
    # SE O USUÁRIO CLICOU EM "SALVAR" NO MODAL
    if request.method == 'POST':
        tipo_acao = request.POST.get('tipo_acao')
        
        if tipo_acao == 'nova_solicitacao':
            # 1. Puxa todos os dados do formulário HTML
            molde_id = request.POST.get('molde_id')
            maquina_id = request.POST.get('maquina_id')
            operador_id = request.POST.get('operador_id')
            ordem_producao = request.POST.get('ordem_producao')
            data_op = request.POST.get('data_op') 
            parecer_producao = request.POST.get('parecer_producao')
            
            # .getlist() captura todos os quadradinhos (checkbox) marcados
            lista_problemas = request.POST.getlist('problemas_ids') 
            
            # 2. Chama o Service para salvar no banco
            SolicitacaoService.abrir_solicitacao(
                molde_id=molde_id,
                maquina_id=maquina_id,
                operador_id=operador_id,
                ordem_producao=ordem_producao,
                parecer_producao=parecer_producao,
                lista_problemas_ids=lista_problemas
            )
            
            messages.success(request, "Solicitação registrada com sucesso!")
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

    pendencias = SolicitacaoManutencao.objects.filter(status='Aberto').order_by('-data_abertura')
    
    context = {
        'pendencias': pendencias,
        'lista_moldes': Molde.objects.filter(status = "Ativo"),
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
    }
    
    return render(request, 'ferramentaria/dashboard.html', context)

# ==============================================================================
# 2. TELA DE HISTÓRICO E REGISTROS
# ==============================================================================
def historico_view(request):
    # Busca todas as ordens, ordenando pelas mais recentes primeiro
    todas_solicitacoes = SolicitacaoManutencao.objects.all().order_by('-data_abertura')
    
    # Se o usuário usou o filtro na tela para buscar um molde específico
    molde_id = request.GET.get('molde_filtro')
    if molde_id:
        todas_solicitacoes = todas_solicitacoes.filter(molde__id=molde_id)
        
    lista_moldes = Molde.objects.filter(status__in=['Operação', 'Manutenção'])

    context = {
        'solicitacoes': todas_solicitacoes,
        'lista_moldes': lista_moldes, # Para preencher o selectbox de filtro
    }
    
    return render(request, 'ferramentaria/historico.html', context)


# ==============================================================================
# 3. TELA DE GERENCIAMENTO (CADASTRAR MOLDES, ETC)
# ==============================================================================
def gerenciamento_view(request):
    # SE O USUÁRIO CLICOU NO BOTÃO "SALVAR" (Método POST)
    if request.method == 'POST':
        # Descobre qual formulário ele enviou (ex: input hidden com nome 'tipo_form')
        tipo_form = request.POST.get('tipo_form')
        
        if tipo_form == 'novo_molde':
            nome = request.POST.get('molde_nome')
            endereco = request.POST.get('endereco_molde')
            status = request.POST.get('status', 'Operação')
            
            # Chama o nosso serviço para fazer a gravação segura!
            if nome and endereco:
                MoldeService.adicionar_molde(nome=nome, endereco=endereco, status=status)
                messages.success(request, f"Molde '{nome}' cadastrado com sucesso!")
            else:
                messages.error(request, "Nome e Endereço são obrigatórios.")
                
            return redirect('gerenciamento') # Recarrega a página para limpar o formulário

    # SE ELE SÓ ABRIU A PÁGINA (Método GET)
    context = {
        'moldes_cadastrados': Molde.objects.all(),
        # Aqui mandaremos as listas de itens, colaboradores, etc., para as abas
    }
    
    return render(request, 'ferramentaria/gerenciamento.html', context)

