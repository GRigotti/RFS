from django.contrib.auth.models import User, Group
from django.db import transaction
from ..models import Colaborador, LogAuditoria

class UsuarioService:
    
    @staticmethod
    @transaction.atomic 
    def adicionar(nome_completo, username, password, nome_grupo, matricula, usuario_logado): # 🟢 MATRÍCULA ADICIONADA AQUI
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

        # 3. Cria automaticamente o "Colaborador"
        Colaborador.objects.create(
            usuario=novo_user,
            nome=nome_completo,
            matricula=matricula, # Agora ele sabe o que é esta variável
            funcao=nome_grupo,
            status='Ativo'
        )

        # 4. Grava o log de auditoria
        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='USUÁRIOS', acao='CRIADO',
            descricao=f"Cadastrou o usuário/colaborador '{nome_completo}' (Login: {username})."
        )
        return novo_user.id

    # 🟢 NOVA FUNÇÃO PARA EDITAR O USUÁRIO
    @staticmethod
    @transaction.atomic
    def alterar(user_id, nome_completo, username, password, nome_grupo, matricula, is_active, usuario_logado):
        user_alvo = User.objects.get(id=user_id)
        
        # Verifica se o novo username já existe (excluindo o próprio utilizador)
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            raise ValueError(f'❌ O login "{username}" já está em uso por outra pessoa.')

        # 1. Atualiza os dados do User (Django)
        user_alvo.username = username
        user_alvo.is_active = (is_active == 'True') # Transforma a string do HTML num booleano
        
        # Só altera a senha se o utilizador digitou algo no campo
        if password: 
            user_alvo.set_password(password)

        # Atualiza as permissões
        if nome_grupo:
            user_alvo.groups.clear()
            grupo, _ = Group.objects.get_or_create(name=nome_grupo)
            user_alvo.groups.add(grupo)
            user_alvo.is_staff = (nome_grupo == 'Admin')
        
        user_alvo.save()

        # 2. Atualiza os dados do Colaborador vinculado
        if hasattr(user_alvo, 'colaborador') and user_alvo.colaborador:
            colab = user_alvo.colaborador
            colab.nome = nome_completo
            colab.matricula = matricula
            colab.funcao = nome_grupo
            colab.status = 'Ativo' if user_alvo.is_active else 'Inativo'
            colab.save()

        LogAuditoria.objects.create(
            usuario=usuario_logado, modulo='USUÁRIOS', acao='EDITADO',
            descricao=f"Alterou o usuário '{nome_completo}' (Login: {username})."
        )
        return True
    
