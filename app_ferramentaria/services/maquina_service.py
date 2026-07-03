from ..models import Maquina, LogAuditoria

class MaquinaService:
    
    @staticmethod
    def adicionar(maquina, grupo_maquina, descricao, status, usuario_logado):
        maquina = maquina.strip().upper()
        grupo_maquina = grupo_maquina.strip().upper() if grupo_maquina else ''
        descricao = descricao.strip() if descricao else ''
        
        # 1. Validação de Regra de Negócio (Duplicidade)
        if Maquina.objects.filter(maquina__iexact=maquina).exists():
            raise ValueError(f"Erro: A máquina '{maquina}' já existe no sistema!")

        # 2. Execução no Banco de Dados
        nova_maquina = Maquina.objects.create(
            maquina=maquina, 
            grupo_maquina=grupo_maquina, 
            descricao=descricao, 
            status=status
        )
        
        # 3. Gravação da Auditoria
        LogAuditoria.objects.create(
            usuario=usuario_logado, 
            modulo='MÁQUINAS', 
            acao='CRIADO', 
            descricao=f"Cadastrou a nova máquina '{maquina}'."
        )
        
        return nova_maquina.id_maquina

    @staticmethod
    def alterar(id_maquina, maquina, grupo_maquina, descricao, status, usuario_logado):
        maquina = maquina.strip().upper()
        
        # 1. Validação de Regra de Negócio (Duplicidade ignorando a própria máquina)
        if Maquina.objects.filter(maquina__iexact=maquina).exclude(id_maquina=id_maquina).exists():
            raise ValueError(f"Erro: O nome '{maquina}' já está sendo usado por outra máquina!")

        # 2. Execução no Banco de Dados
        linhas_afetadas = Maquina.objects.filter(id_maquina=id_maquina).update(
            maquina=maquina,
            grupo_maquina=grupo_maquina.strip().upper() if grupo_maquina else '',
            descricao=descricao.strip() if descricao else '',
            status=status
        )
        
        # 3. Gravação da Auditoria
        LogAuditoria.objects.create(
            usuario=usuario_logado, 
            modulo='MÁQUINAS', 
            acao='EDITADO', 
            descricao=f"Alterou a máquina '{maquina}' (ID: {id_maquina}). Status: {status}."
        )
        
        return linhas_afetadas > 0