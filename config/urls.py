from django.contrib import admin
from django.urls import path, include


# 1. Muda o texto que aparece na aba do navegador
admin.site.site_title = 'Painel de Controle - FRAMES'

# 2. Muda o subtítulo na tela inicial do admin (o antigo "Administração do Site")
admin.site.index_title = 'Controle de usuarios'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_ferramentaria.urls')), 
]