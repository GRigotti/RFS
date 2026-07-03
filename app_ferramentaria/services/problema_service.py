from ..models import Problema, LogAuditoria

class ProblemaService:
    
    @staticmethod
    def adicionar(problema, descricao, usuario_logado):
        texto_problema = problema.strip()
        
        novo = Problema.objects.create(
            problema=texto_problema, 
            descricao=descricao.strip() if descricao else ''
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='PROBLEMAS', acao='CRIADO',
            descricao=f"Cadastrou o novo problema '{texto_problema}'."
        )
        return novo.id

    @staticmethod
    def alterar(id_problema, problema, descricao, usuario_logado):
        texto_problema = problema.strip()
        
        linhas_afetadas = Problema.objects.filter(id=id_problema).update(
            problema=texto_problema,
            descricao=descricao.strip() if descricao else ''
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='PROBLEMAS', acao='EDITADO',
            descricao=f"Alterou o problema '{texto_problema}' (ID: {id_problema})."
        )
        return linhas_afetadas > 0