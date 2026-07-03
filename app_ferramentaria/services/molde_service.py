from django.db import transaction
from ..models import Molde, LogAuditoria

class MoldeService:
    
    @staticmethod
    @transaction.atomic
    def adicionar(molde_nome, endereco_molde, status, usuario_logado):
        molde_nome = molde_nome.strip().upper()
        endereco_molde = endereco_molde.strip().upper() if endereco_molde else ''
        
        if Molde.objects.filter(molde_nome__iexact=molde_nome).exists():
            raise ValueError(f"Erro: O molde '{molde_nome}' já existe no sistema!")

        novo_molde = Molde.objects.create(
            molde_nome=molde_nome,
            endereco_molde=endereco_molde,
            status=status
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='MOLDES', acao='CRIADO',
            descricao=f"Cadastrou o novo molde '{molde_nome}'."
        )
        return novo_molde.id

    @staticmethod
    @transaction.atomic
    def alterar(id_molde, molde_nome, endereco_molde, status, usuario_logado):
        molde_nome = molde_nome.strip().upper()
        endereco_molde = endereco_molde.strip().upper() if endereco_molde else ''
        
        if Molde.objects.filter(molde_nome__iexact=molde_nome).exclude(id=id_molde).exists():
            raise ValueError(f"Erro: O nome '{molde_nome}' já está em uso por outro molde!")

        linhas_afetadas = Molde.objects.filter(id=id_molde).update(
            molde_nome=molde_nome,
            endereco_molde=endereco_molde,
            status=status
        )
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='MOLDES', acao='EDITADO',
            descricao=f"Alterou o molde '{molde_nome}' (ID: {id_molde}). Status: {status}."
        )
        return linhas_afetadas > 0