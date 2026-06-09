import os
from pathlib import Path

# Constrói os caminhos relativos da sua pasta (Assim funciona em qualquer computador)
BASE_DIR = Path(__file__).resolve().parent.parent

# Chave de segurança gerada pelo Django (Não compartilhe em produção)
SECRET_KEY = 'django-insecure-chave-padrao-de-desenvolvimento-soprano'

# Modo de depuração ligado para vermos os erros detalhados enquanto programamos
DEBUG = True

ALLOWED_HOSTS = ['giovanirigotti.pythonanywhere.com', '127.0.0.1', 'localhost']

# ==============================================================================
# APLICATIVOS INSTALADOS
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Nosso aplicativo industrial!
    'app_ferramentaria', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Aponta para a "mesa telefônica" principal de links
ROOT_URLCONF = 'config.urls'

# ==============================================================================
# CONFIGURAÇÃO DAS TELAS (HTML)
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app_ferramentaria' / 'templates'], # Onde vamos colocar o base.html
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==============================================================================
# BANCO DE DADOS (A sua configuração aplicada da forma mais segura)
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # Em vez de chumbar o 'C:\Users...', o BASE_DIR acha o arquivo onde quer que a pasta esteja!
        'NAME': BASE_DIR / 'cmms_industrial.db', 
    }
}

# ==============================================================================
# IDIOMA E FUSO HORÁRIO (Ajustado para o Brasil)
# ==============================================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos (CSS, Imagens, JavaScript)
STATIC_URL = 'static/'

# Padrão de ID do Django
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'