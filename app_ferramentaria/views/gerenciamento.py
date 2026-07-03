import traceback
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User, Group

from ..models import ItemPorMolde, Molde, Maquina, Colaborador, Problema, AcaoManutencao
from ..services import (
    MoldeService, ItemService, MaquinaService,  ProblemaService, AcaoManutencaoService, UsuarioService
)

@never_cache
@login_required(login_url='ferramentaria:login')
@csrf_protect
def gerenciamento_view(request):
    is_admin = (request.user.is_superuser or request.user.is_staff or 
                request.user.has_perm('app_ferramentaria.change_molde') or 
                request.user.groups.filter(name='Admin').exists())
    if not is_admin:
        messages.error(request, '❌ Acesso negado: Você não tem permissão para acessar o Gerenciamento.')
        return redirect('ferramentaria:dashboard')
    
    context = {
        'colaboradores': Colaborador.objects.all().order_by('nome'),
        'maquinas': Maquina.objects.all().order_by('maquina'),
        'acoes': AcaoManutencao.objects.all().order_by('acao'),
        'moldes': Molde.objects.all().order_by('molde_nome'),
        'itens_molde': ItemPorMolde.objects.all().order_by('item_codigo'),
        'problemas': Problema.objects.all().order_by('problema'),
        'usuarios_sistema': User.objects.all().order_by('username'),
    }
    return render(request, 'ferramentaria/gerenciamento.html', context)

def salvar_molde(request):

    if request.method == 'POST':
        try:
            id_reg = request.POST.get('id')
            kwargs = {
                'molde_nome': request.POST.get('molde_nome'),
                'endereco_molde': request.POST.get('endereco_molde'),
                'status': request.POST.get('status', 'Ativo'),
                'usuario_logado': request.user
            }
            
            if id_reg:
                MoldeService.alterar(id_molde=id_reg, **kwargs)
                messages.success(request, "Molde atualizado com sucesso!")
            else:
                MoldeService.adicionar(**kwargs)
                messages.success(request, "Novo molde cadastrado com sucesso!")
                
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('/gerenciamento/?aba=aba-moldes')

def salvar_item_molde(request):
    if request.method == 'POST':
        try:
            id_reg = request.POST.get('id')
            kwargs = {
                'id_ref_molde': request.POST.get('id_referencia_molde'),
                'item_codigo': request.POST.get('item_codigo'),
                'descricao': request.POST.get('descricao'),
                'cod_complementar': request.POST.get('cod_complementar'),
                'linha': request.POST.get('linha'),
                'status': request.POST.get('status', 'Ativo'),
                'usuario_logado': request.user
            }
            
            if id_reg:
                ItemService.alterar(id_item=id_reg, **kwargs)
                messages.success(request, "Item de molde atualizado com sucesso!")
            else:
                ItemService.adicionar(**kwargs)
                messages.success(request, "Novo item cadastrado com sucesso!")
                
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('/gerenciamento/?aba=aba-itens-molde')

def salvar_maquina(request):
    if request.method == 'POST':
        try:
            id_reg = request.POST.get('id')
            kwargs = {
                'maquina': request.POST.get('maquina'),
                'grupo_maquina': request.POST.get('grupo_maquina'),
                'descricao': request.POST.get('descricao'),
                'status': request.POST.get('status', 'Ativo'),
                'usuario_logado': request.user # Passamos o usuário para o Service gerar o log!
            }
            
            if id_reg:
                MaquinaService.alterar(id_maquina=id_reg, **kwargs)
                messages.success(request, "Máquina atualizada com sucesso!")
            else:
                MaquinaService.adicionar(**kwargs)
                messages.success(request, "Nova máquina cadastrada com sucesso!")
                
        except ValueError as e:
            # Se o Service barrar a operação (ex: nome duplicado), cai aqui
            messages.error(request, str(e))
            
    return redirect('/gerenciamento/?aba=aba-maquinas')

def salvar_problema(request):
    if request.method == 'POST':
        try:
            id_reg = request.POST.get('id')
            kwargs = {
                'problema': request.POST.get('problema'),
                'descricao': request.POST.get('descricao'),
                'usuario_logado': request.user
            }
            
            if id_reg:
                ProblemaService.alterar(id_problema=id_reg, **kwargs)
                messages.success(request, "Problema atualizado com sucesso!")
            else:
                ProblemaService.adicionar(**kwargs)
                messages.success(request, "Novo problema cadastrado com sucesso!")
                
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('/gerenciamento/?aba=aba-problemas')

def salvar_acao(request):
    if request.method == 'POST':
        try:
            id_reg = request.POST.get('id')
            kwargs = {
                'acao': request.POST.get('acao'),
                'usuario_logado': request.user
            }
            
            if id_reg:
                AcaoManutencaoService.alterar(id_acao=id_reg, **kwargs)
                messages.success(request, "Ação técnica atualizada com sucesso!")
            else:
                AcaoManutencaoService.adicionar(**kwargs)
                messages.success(request, "Nova ação técnica cadastrada com sucesso!")
                
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('/gerenciamento/?aba=aba-acoes')

def salvar_usuario(request):
    if request.method == 'POST':
        tipo_acao = request.POST.get('tipo_acao')

        if tipo_acao == 'criar_usuario':
            try:
                UsuarioService.adicionar(
                    nome_completo=request.POST.get('nome_completo', '').strip(),
                    username=request.POST.get('username', '').strip(),
                    password=request.POST.get('password', ''),
                    nome_grupo=request.POST.get('grupo', ''),
                    usuario_logado=request.user
                )
                messages.success(request, f'✅ Usuário cadastrado com sucesso!')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erro interno: {str(e)}')

        elif tipo_acao == 'alternar_status_usuario':
            try:
                user_id = request.POST.get('user_id')
                UsuarioService.alternar_status(
                    user_id=user_id,
                    usuario_logado=request.user
                )
                messages.success(request, 'Status do usuário modificado!')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erro interno: {str(e)}')

        elif tipo_acao == 'alterar_funcao':
            try:
                UsuarioService.alterar_funcao(
                    user_id=request.POST.get('user_id'),
                    novo_nome_grupo=request.POST.get('grupo'),
                    usuario_logado=request.user
                )
                messages.success(request, '✅ Função do usuário atualizada!')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar função: {str(e)}')

    return redirect('/gerenciamento/?aba=aba-usuarios')