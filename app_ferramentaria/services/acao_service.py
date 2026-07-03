from ..models import AcaoManutencao, LogAuditoria

class AcaoManutencaoService:
    
    @staticmethod
    def adicionar(acao, usuario_logado):
        texto_acao = acao.strip()
        
        nova = AcaoManutencao.objects.create(acao=texto_acao)
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='AÇÕES TÉCNICAS', acao='CRIADO',
            descricao=f"Cadastrou a nova ação '{texto_acao}'."
        )
        return nova.id

    @staticmethod
    def alterar(id_acao, acao, usuario_logado):
        texto_acao = acao.strip()
        
        linhas_afetadas = AcaoManutencao.objects.filter(id=id_acao).update(acao=texto_acao)
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='AÇÕES TÉCNICAS', acao='EDITADO',
            descricao=f"Alterou a ação '{texto_acao}' (ID: {id_acao})."
        )
        return linhas_afetadas > 0