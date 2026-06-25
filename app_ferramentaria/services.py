import os

from .models import Molde, ItemPorMolde, Maquina, Colaborador, Problema, AcaoManutencao, SolicitacaoManutencao, SolicitacaoAcao
from django.db import transaction  # type: ignore[reportMissingModuleSource]
from django.utils import timezone
from .models import LogAuditoria

class MoldeService:
    
    @staticmethod
    @transaction.atomic # Garante que molde e itens salvem juntos. Se der erro, desfaz tudo (equivalente ao session.rollback)
    def adicionar_molde(nome, endereco, status="Operação", itens_iniciais=None):
        # 1. Cria o molde (o Django já gera e retorna o objeto com ID)
        novo_molde = Molde.objects.create(molde_nome=nome, endereco_molde=endereco, status=status)
        
        # 2. Se houver itens, cria vinculando ao objeto molde
        if itens_iniciais:
            for item in itens_iniciais:
                ItemPorMolde.objects.create(
                    molde=novo_molde,
                    item_codigo=item.get('item_codigo'),
                    descricao=item.get('descricao', ''),
                    linha=item.get('linha', ''),
                    status="Ativo"
                )
        return novo_molde.id

    @staticmethod
    @transaction.atomic
    def alterar_molde(id_molde, itens_modificados=None, **kwargs):
        try:
            molde = Molde.objects.get(id=id_molde)
            
            # Atualiza os dados principais do molde
            for chave, valor in kwargs.items():
                if hasattr(molde, chave) and valor is not None:
                    setattr(molde, chave, valor)
            molde.save()

            # Processa os itens
            if itens_modificados:
                for item in itens_modificados:
                    id_item = item.get('id_item')
                    if id_item:
                        # Situação A: Atualiza item existente via Dicionário Desempacotado
                        ItemPorMolde.objects.filter(id_item=id_item, molde=molde).update(
                            **{k: v for k, v in item.items() if k != 'id_item'}
                        )
                    else:
                        # Situação B: Cria novo item
                        ItemPorMolde.objects.create(
                            molde=molde,
                            item_codigo=item.get('item_codigo'),
                            descricao=item.get('descricao', ''),
                            linha=item.get('linha', ''),
                            status=item.get('status', 'Ativo')
                        )
            return True
        except Molde.DoesNotExist:
            return False

class ItemService:
    @staticmethod
    def adicionar_item(id_molde, item_codigo, descricao="", linha=""):
        molde = Molde.objects.get(id=id_molde)
        novo_item = ItemPorMolde.objects.create(
            molde=molde, item_codigo=item_codigo, descricao=descricao, linha=linha, status="Ativo"
        )
        return novo_item.id_item

    @staticmethod
    def alterar_item(id_item, **kwargs):
        # O Django permite atualizar direto sem buscar o objeto antes
        linhas_afetadas = ItemPorMolde.objects.filter(id_item=id_item).update(**kwargs)
        return linhas_afetadas > 0

class ColaboradorService:
    @staticmethod
    def adicionar(nome, funcao):
        funcao_ajustada = funcao.strip().capitalize()
        colab = Colaborador.objects.create(nome=nome, funcao=funcao_ajustada)
        return colab.id

    @staticmethod
    def alterar(id_colaborador, **kwargs):
        if 'funcao' in kwargs and kwargs['funcao']:
            kwargs['funcao'] = kwargs['funcao'].strip().capitalize()
            
        afetados = Colaborador.objects.filter(id=id_colaborador).update(**kwargs)
        return afetados > 0

class MaquinaService:
    @staticmethod
    def adicionar(nome_maquina):
        maquina = Maquina.objects.create(maquina=nome_maquina)
        return maquina.id_maquina

    @staticmethod
    def alterar(id_maquina, **kwargs):
        afetados = Maquina.objects.filter(id_maquina=id_maquina).update(**kwargs)
        return afetados > 0
    
    class ProblemaService:
        @staticmethod
        def adicionar(descricao_problema):
            novo = Problema.objects.create(problema=descricao_problema)
            return novo.id

        @staticmethod
        def alterar(id_problema, **kwargs):
            afetados = Problema.objects.filter(id=id_problema).update(**kwargs)
            return afetados > 0


    class AcaoManutencaoService:
        @staticmethod
        def adicionar(descricao_acao):
            nova = AcaoManutencao.objects.create(acao=descricao_acao)
            return nova.id

        @staticmethod
        def alterar(id_acao, **kwargs):
            afetados = AcaoManutencao.objects.filter(id=id_acao).update(**kwargs)
            return afetados > 0
        
        # ==============================================================================
# SERVIÇO PRINCIPAL: ORDENS DE SERVIÇO (CHAMADOS)
# ==============================================================================

class SolicitacaoService:
    
    @staticmethod
    @transaction.atomic
    def abrir_solicitacao( molde_id, maquina_id, item_id, operador_id, ordem_manutencao, parecer_producao, lista_problemas_ids=None, usuario_logado=None):
        """
        Cria uma nova OS. Usado pelo modal 'Nova Solicitação'.
        """
        # 1. Cria o registro principal da solicitação
        nova_os = SolicitacaoManutencao.objects.create(
            molde_id=molde_id,  # O Django entende o sufixo _id para ForeignKeys
            maquina_id=maquina_id,
            item_id=item_id,
            operador_id=operador_id,
            # ordem_producao=ordem_producao,
            ordem_manutencao=ordem_manutencao,
            parecer_producao=parecer_producao,
            status='Aberto',
        )
        
        # 2. Se o operador marcou os problemas (checkboxes/selects), faz a ligação (Many-to-Many)
        if lista_problemas_ids:
            nova_os.problemas.set(lista_problemas_ids)

        LogAuditoria.objects.create(
            usuario=usuario_logado,
            modulo='SOLICITAÇÕES',
            acao='CRIADO',
            descricao=f'Abriu a Ficha nº {nova_os.id} para o molde ID {molde_id}.'
        )

        return nova_os.id
    

    @staticmethod
    @transaction.atomic
    def registrar_manutencao(os_id, responsavel_id, parecer_ferramentaria, novo_status, lista_acoes_ids, motivo=None, previsao=None, usuario_logado=None):
        # 1. Busca a Ordem de Serviço aberta que está sendo tratada
        os_obj = SolicitacaoManutencao.objects.get(id=os_id)

        # 2. Atualiza os campos preenchidos pelo ferramenteiro
        os_obj.responsavel_id = responsavel_id if responsavel_id else None
        os_obj.parecer_ferramentaria = parecer_ferramentaria
        os_obj.status = novo_status  # Grava dinamicamente "Em Manutenção" ou "Concluído"
        os_obj.motivo_manutencao = motivo
        os_obj.previsao_retorno = previsao

        # Se o status estiver sendo alterado para Concluído, grava o carimbo de data/hora atual
        if novo_status == 'Concluído':
            from django.utils import timezone
            os_obj.data_fechamento = timezone.now()

        # 3. Salva a alteração da linha do registro principal no banco SQLite
        os_obj.save()

        # ==========================================================================
        # 🟢 4. CORREÇÃO DEFINITIVA: GRAVAÇÃO MANUAL NA TABELA INTERMEDIÁRIA
        # ==========================================================================

        # Passo A: Remove do banco qualquer ação que estivesse previamente vinculada a esta OS
        SolicitacaoAcao.objects.filter(solicitacao=os_obj).delete()

        # Passo B: Percorre a lista de IDs vindas do modal e cria as novas linhas uma a uma
        if lista_acoes_ids:
            for acao_id in lista_acoes_ids:
                if acao_id:  # Valida se o ID não é nulo ou vazio
                    SolicitacaoAcao.objects.create(
                        solicitacao=os_obj,
                        acao_id=int(acao_id)
                    )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado,
            modulo='SOLICITAÇÕES',
            acao='STATUS_ALTERADO',
            descricao=f'Atualizou a Ficha nº {os_id} para o status "{novo_status}".'
        )