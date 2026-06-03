from django.urls import path
from . import views

app_name = 'ferramentaria'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('historico/', views.historico_view, name='historico'),
    path('gerenciamento/', views.gerenciamento_view, name='gerenciamento'),
]