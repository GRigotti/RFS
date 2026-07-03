from django.db import transaction
from django.utils import timezone
from ..models import SolicitacaoManutencao, SolicitacaoAcao, LogAuditoria

class SolicitacaoService:
    
    @staticmethod
    @transaction.atomic
    def abrir_solicitacao(molde_id, maquina_id, item_id, operador_id, ordem_manutencao, parecer_producao, lista_problemas_ids=None, usuario_logado=None):
        nova_os = SolicitacaoManutencao.objects.create(
            molde_id=molde_id,
            maquina_id=maquina_id,
            item_id=item_id,
            operador_id=operador_id,
            ordem_manutencao=ordem_manutencao,
            parecer_producao=parecer_producao,
            status='Aberto',
        )
        
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
        os_obj = SolicitacaoManutencao.objects.get(id=os_id)

        os_obj.responsavel_id = responsavel_id if responsavel_id else None
        os_obj.parecer_ferramentaria = parecer_ferramentaria
        os_obj.status = novo_status  
        os_obj.motivo_manutencao = motivo
        os_obj.previsao_retorno = previsao

        if novo_status == 'Concluído':
            os_obj.data_fechamento = timezone.now()

        os_obj.save()

        SolicitacaoAcao.objects.filter(solicitacao=os_obj).delete()

        if lista_acoes_ids:
            for acao_id in lista_acoes_ids:
                if acao_id:  
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