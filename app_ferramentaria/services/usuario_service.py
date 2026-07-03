from django.contrib.auth.models import User, Group
from django.db import transaction
from ..models import Colaborador, LogAuditoria

class UsuarioService:
    
    @staticmethod
    @transaction.atomic # Garante que User e Colaborador sejam salvos juntos
    def adicionar(nome_completo, username, password, nome_grupo, usuario_logado):
        if User.objects.filter(username=username).exists():
            raise ValueError(f'❌ O login "{username}" já está em uso.')

        # 1. Cria a conta de acesso no Django
        novo_user = User.objects.create_user(username=username, password=password)
        if nome_grupo == 'Admin':
            novo_user.is_staff = True
            novo_user.save()

        # 2. Atribui o grupo de permissões
        if nome_grupo:
            grupo, _ = Group.objects.get_or_create(name=nome_grupo)
            novo_user.groups.add(grupo)

        # 3. Cria automaticamente o "Colaborador" vinculado para uso nas OS
        Colaborador.objects.create(
            usuario=novo_user,
            nome=nome_completo,
            funcao=nome_grupo,
            status='Ativo'
        )

        # 4. Grava o log de auditoria
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='USUÁRIOS', acao='CRIADO',
            descricao=f"Cadastrou o usuário/colaborador '{nome_completo}' (Login: {username})."
        )
        return novo_user.id

    @staticmethod
    @transaction.atomic
    def alternar_status(user_id, usuario_logado):
        user_alvo = User.objects.get(id=user_id)
        
        if user_alvo == usuario_logado:
            raise ValueError('❌ Você não pode inativar a si mesmo.')

        # Inverte o status de acesso do sistema
        novo_status_ativo = not user_alvo.is_active
        user_alvo.is_active = novo_status_ativo
        user_alvo.save()

        # Se este usuário tiver um colaborador vinculado, inativa ele também nas listas
        if hasattr(user_alvo, 'colaborador') and user_alvo.colaborador:
            user_alvo.colaborador.status = 'Ativo' if novo_status_ativo else 'Inativo'
            user_alvo.colaborador.save()

        texto_status = 'Ativado' if novo_status_ativo else 'Inativado'
        
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='USUÁRIOS', acao='STATUS ALTERADO',
            descricao=f"O usuário '{user_alvo.username}' foi {texto_status}."
        )
        return novo_status_ativo
    
    @staticmethod
    @transaction.atomic
    def alterar_funcao(user_id, novo_nome_grupo, usuario_logado):
        user_alvo = User.objects.get(id=user_id)
        
        # 1. Atualiza o Grupo de permissões no Django
        if novo_nome_grupo:
            # Remove de todos os grupos anteriores
            user_alvo.groups.clear()
            # Adiciona ao novo grupo
            grupo, _ = Group.objects.get_or_create(name=novo_nome_grupo)
            user_alvo.groups.add(grupo)
            
            # Ajusta o is_staff se for Admin
            user_alvo.is_staff = (novo_nome_grupo == 'Admin')
            user_alvo.save()

        # 2. Atualiza a função na tabela Colaborador (para manter sincronizado)
        if hasattr(user_alvo, 'colaborador'):
            colab = user_alvo.colaborador
            colab.funcao = novo_nome_grupo
            colab.save()

        # 3. Log de auditoria
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='USUÁRIOS', acao='FUNÇÃO ALTERADA',
            descricao=f"Alterou a função do usuário '{user_alvo.username}' para '{novo_nome_grupo}'."
        )
        return True