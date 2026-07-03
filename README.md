# Relatório de Estruturação: CRMF (Sistema de Controle e Registro de Manutenção de Ferramentas)

---

## Visão Geral

O CRMF é uma plataforma de gestão industrial desenvolvida em Django, focada na rastreabilidade de moldes, ordens de manutenção e gestão de ativos de ferramentaria. A arquitetura atual segue o padrão Service Layer, garantindo desacoplamento entre a interface do usuário (Views) e as regras de negócio (Services).
<br>

## Estrutura de Pastas e Bibliotecas

    CMRF/
    ├── app_ferramentaria/
    │   ├── services/
    │   │   ├── __init__.py             # Exportador de serviços
    │   │   ├── molde_service.py        # Lógica: Molde/Item
    │   │   ├── item_service.py         # Lógica: Item por Molde
    │   │   ├── maquina_service.py      # Lógica: Cadastro de Máquinas
    │   │   ├── problema_service.py     # Lógica: Cadastro de Problemas
    │   │   ├── acao_service.py         # Lógica: Cadastro de Ações Técnicas
    │   │   ├── solicitacao_service.py  # Lógica: Ciclo de Manutenção (OS)
    │   │   └── usuario_service.py      # Lógica: Auth, Usuário, Colaborador
    │   ├── views/
    │   │   ├── __init__.py             # Exportador de views
    │   │   ├── dashboard.py            # Dashboard (CBV/Função)
    │   │   ├── historico.py            # Histórico/KPIs
    │   │   └── gerenciamento.py        # Endpoints de Salvar (Ação delegada)
    │   ├── templates/
    │   │   ├── admin/
    │   │   │   └── base_site.html      # Base para interface do painel Admin do Django
    │   │   └── ferramentaria/
    │   │       ├── base.html           # Base do layout do site
    │   │       ├── dashboard.html      # Página Home
    │   │       ├── gerenciamento.html  # Página de Gerenciamento
    │   │       ├── historico.html      # Página de Detalhes
    │   │       └── login.html          # Página de Login
    │   ├── models.py                   # Definição das tabelas
    │   └─ urls.py                      # Roteamento local
    ├── config/
    │   ├── settings.py                 # Configurações do Django
    │   └── urls.py                     # Roteamento global
    ├── manage.py                       # Utilitário de comando
    └── cmms_industrial.db              # Banco SQLite
<br>

## CRMF(Back-End)

Este projeto utiliza uma arquitetura modular baseada em Service Layer, garantindo que as regras de negócio sejam isoladas da camada de apresentação (Views).
<br>

### /app_ferramentaria/

O diretório app_ferramentaria encapsula toda a lógica de negócio, persistência e interface do seu sistema de gestão de ferramentaria.
<br>

#### /app_ferramentaria/services

Função Técnica: Centraliza toda a lógica de processamento, validação de dados, transações atómicas (garantindo a integridade do banco de dados) e auditoria.
Papel: Atua como o "cérebro" do sistema. As Views delegam aqui todas as operações que envolvem escrita no banco, transformações de dados ou aplicação de regras específicas.

    __init__.py: Módulo de exportação e centralização.

    molde_service.py: Gerencia o cadastro e integridade dos Moldes. Valida duplicidade e registra logs de auditoria para cada alteração.

    item_service.py: Controla os itens dos moldes, garantindo unicidade e correta associação.

    maquina_service.py: Padroniza o cadastro de máquinas, aplicando formatação e registros de auditoria.

    problema_service.py: Mantém a base de defeitos/problemas para padronização de diagnósticos nas manutenções.

    acao_service.py: Gerencia o catálogo de ações corretivas realizadas pela ferramentaria.

    solicitacao_service.py: O componente principal. Orquestra a abertura, o registro de ações e o fechamento de Ordens de Serviço (OS), garantindo consistência via transações.

    usuario_service.py: Unifica a gestão de usuários e colaboradores. Garante que qualquer novo acesso criado tenha um perfil de colaborador vinculado para rastreabilidade nas OSs.
<br>

#### /app_ferramentaria/views

Função Técnica: Gerencia o ciclo de vida da requisição HTTP. Recebe o request do usuário, extrai os parâmetros (via POST ou GET), invoca o Service correspondente e retorna uma resposta (renderização de template ou JSON).
Papel: Atua como uma "casca fina". O objetivo é que estas funções contenham a menor quantidade possível de lógica de negócio. Elas não devem saber como um molde é salvo, apenas que ele deve ser salvo chamando o MoldeService.

    __init__.py: Módulo de exportação e centralização.

    dashboard.py: Controlador da página principal (Landing Page do sistema).

    historico.py: Controlador da página de Detalhes(relatórios, KPIs e análise de dados)alterações cadastrais

    gerenciamento.py: Controlador da página de Gerenciamento( parte administrativa do sistema, controle de cadastros)
<br>

#### /app_ferramentaria/models.py

    Função Técnica: Define a estrutura relacional do seu banco de dados utilizando o ORM (Object-Relational Mapping) do Django.
    Papel: Atua como o "modelo da realidade". Define as classes que representam suas tabelas (ex: SolicitacaoManutencao, Molde, LogAuditoria) e as relações entre elas (Many-to-Many, ForeignKey). É aqui que você define as restrições de campo, como max_length, null=True, ou chaves únicas.
<br>

#### /app_ferramentaria/urls.py

    Função Técnica: Mapeia as URLs digitadas pelo usuário para as funções dentro da pasta views/.
    Papel: Atua como o "direcionador". Define os caminhos acessíveis no seu sistema (ex: /gerenciamento/, /historico/) e nomeia cada rota (name='...'), permitindo que você altere o link no HTML sem precisar atualizar  
           todos os arquivos do projeto.
<br>

### /config/

Responsável por manter o Django configurado, conectado ao banco de dados.

    settings.py: Define como o Django se comporta. Contém segredos de segurança, permissões de acesso.

    urls.py: Roteador principal (Ponto de entrada), ele mapeia as URLs globais.

### /manage.py

Utilitário administrativo de linha de comando.
<br>

### /cmmn_industiral.db

Banco de dados relacional(SQLite).
Arquivo físico onde todas as informações do seu sistema residem (dados dos moldes, registros de manutenção, contas de usuários e logs).
<br>

## Interface(Front-End)

### /templates/admin/

    base_site.html: Sobrescrita do tema administrativo do Django.
<br>

### /templates/ferramentaria

    base.html: Layout base (Master Page).

    dashboard.html: Página principal de operação.

    historico.html: Central de relatórios e indicadores.

    login.html: Portal de autenticação.
<br>

---

# Manual de Operação: Sistema de Gestão de Ferramentaria CRMF (Sistema de Controle e Registro de Manutenção de Ferramentas)

---

## Home

Bloco Solicitações
    Contadores (Abertas | Concluídas): Mostra o resumo rápido de movimentações no período selecionado.
    Campos de Período (Data Início e Data Fim): Defina o intervalo de datas que deseja analisar.
    Botão "Filtrar": Após selecionar as datas, clique aqui para atualizar os contadores, a lista de solicitações em aberto e os dados dos gráficos. Sem clicar aqui após alterar as datas, o painel não atualizará.

Botão Reg Solicitação
    Botão de ação rápida para abrir o formulário onde você registrará uma nova ocorrência de manutenção. É o ponto de entrada para qualquer problema encontrado na ferramentaria.

Bloco Solicitações em Aberto
    Exibe em tempo real o que está pendente de solução.
    Lista o ID/Nome do Molde, o Problema reportado e a Data de abertura.
    Nesse bloco tambem é possivel registar que o molde esta em manutenção ou foi conlcuido. Cliando na solicitação abrira um formulario para precher os dados e modificar a situação do processo.

Bloco Analisar Molde
    Ferramenta para verificar informações rapidas do molde, como itens, enderços e contador e distribuição de problemas
    Para selecionar um molde, clique no menu suspenço e escolha o molde a analisar.

## Detalhes

Campo "Consultar Histórico": Ao selecionar "TODOS" esta tela gera  KPIs (Indicadores de Performance)

### Gráficos de Performance

    Situação das Demandas: Mostra a saúde da ferramentaria (quantos moldes estão prontos vs. quantos estão parados).

    Top 5 Moldes: Identifica rapidamente quais ativos estão consumindo mais tempo da equipe técnica.

    Principais Defeitos: Mostra os problemas "campeões" da fábrica. Se a barra de "REBARBA NAS CAVIDADES" estiver muito alta, é um sinal de alerta para a engenharia de processo.

    MTTR (Tempo Médio de Reparo): Mede a eficiência. Se essa linha estiver subindo, significa que a equipe está demorando mais para consertar os moldes

### Item

Ao selecionar um molde específico (como o MI0015 no exemplo), a tela transforma-se em um Prontuário do Molde.
    Painel "Itens Vinculados": Mostra a estrutura técnica desse molde específico (peças/cavidades que compõem a ferramenta).

    Linha do Tempo de Manutenções: Permite que você veja o histórico completo de intervenções em ordem cronológica. Se um molde volta para a ferramentaria com o mesmo problema de uma semana atrás, essa lista vai confirmar o histórico imediatamente.

Graficos os itens

Principal defeitos: Mostra a lista com principais defeitos

Tempo medio de manutenção:  Tempo que demora para ser feita a manutenção do molde

## Gerenciamento

    Campo Filtro para buscar informações na tabela, buscando na primeira coluna.

Tabelas

    Usuarios: Gerencia os acesso e permições doss  usuarios.

    Máquinas: Gerencia as informações relacionadas as maquinas.

    Moldes: Gerencia as informações dos moldes.

    Itens por Molde: Gerencia as informações dos itens.

    Ações: Gerencia as ações a serem tomadas.

    Problemas: Gerencia os problemas identificados.

Todas as tabelas tem um botão para cadastrar os elementos, cada um com seu formulario.
Eceto a tabela usuarios, cada item tem um botão "Editar" que permite alterar as informações.
Na tabela Usuarios, tem um botão para inativar o usuario e um campo para selecionar a função.
