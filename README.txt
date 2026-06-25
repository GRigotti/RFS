Alterações da Versão 0.4.6

Views.py

    Modifica forma de contar de ordem criadas para abertas 
    Criado logica para alimentar gráfico MTTR

base.html

    Modificado títulos das telas
    Adicionado CSS para mensagem de erro
    Adicionando mensagem de confirmação de registro
    modificado sistema de notificações

dashboard.html

    modificado nome do balanço para solicitações
    Modificado titulo de pendencias para solicitações em aberto
    Removido mensagem de notificação

historico.html

    modificado títulos "TODOS ( Apenas Dashboard Gerencias)" para "TODOS"
    Adicionado gráfico Mean Time to Repair - MTTR
    Ajustado cores dos rótulos aberto, manutenção e concluído.

Versão 0.4.7

    Removido campos de Ordem de produção e data Op das solicitações.
    Adicionado campo Ordem de Manutenção.
    Limitado o numero de Solicitações abertas por molde para uma.

Versão 0.5 

    Adicionado funções de login(usuários)
    Adicionado permissões para criação ou alteração de conteúdo

Versão 0.5.1

    Modificado cabeçario para logo da Soprano

Versão 0.5.2

    dashboard:
    Adicionado IN em analisar molde
    Adicionado campo para selecionar IN
    Adicionado campo previsão e aguardando por para status "Em manutenção"


    histórico:
    Adicionado informação in
    Adicionado campo para selecionar IN
    Adicionado campo previsão e aguardando por para status "Em manutenção"

    views:
    adicionado logica para buscar IN
    adicionado estrutura para a previsão

    Geral:
    Adicionado logs para controlar login, Solicitações, usuarios, moldes, itens, maquinas, problemas, ações.

