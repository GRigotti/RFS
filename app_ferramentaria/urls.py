from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'ferramentaria'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('historico/', views.historico_view, name='historico'),
    path('gerenciamento/', views.gerenciamento_view, name='gerenciamento'),
    # Endpoints genéricos para salvar/editar (exemplo para duas tabelas, replique para as outras)
    path('gerenciamento/maquina/salvar/', views.salvar_maquina, name='salvar_maquina'),
    path('gerenciamento/acao/salvar/', views.salvar_acao, name='salvar_acao'),
    path('gerenciamento/molde/salvar/', views.salvar_molde, name='salvar_molde'),
    path('gerenciamento/item-molde/salvar/', views.salvar_item_molde, name='salvar_item_molde'),
    path('gerenciamento/problema/salvar/', views.salvar_problema, name='salvar_problema'),
    path('login/', auth_views.LoginView.as_view(template_name='ferramentaria/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='ferramentaria:login'), name='logout'),
    path('salvar_usuario/', views.salvar_usuario, name='salvar_usuario'),
    path('ajax/carregar-itens/', views.carregar_itens_por_molde, name='carregar_itens_molde'),
]