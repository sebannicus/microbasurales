"""
Django settings para desarrollo LOCAL del proyecto Microbasurales.
Esta versión NO usa AWS, NO usa PythonAnywhere y NO usa RDS.
Funciona con PostgreSQL LOCAL + STATICFILES + MEDIA en tu PC.
"""

import os
from pathlib import Path
from datetime import timedelta

# ========================================
# BASE DIR
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================================
# SECURITY (LOCAL)
# ========================================
SECRET_KEY = "dev-secret-key-no-importa-en-local"
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = []

# ========================================
# APPS
# ========================================
INSTALLED_APPS = [
    # Django base
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'corsheaders',

    # Apps del proyecto
    'usuarios',
    'denuncias',
    'analitica',
]

# ========================================
# MIDDLEWARE
# ========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # OK en local
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================================
# URLS / WSGI
# ========================================
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ========================================
# BASE DE DATOS LOCAL (POSTGRESQL LOCAL)
# ========================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "microbasurales",    # Nombre de tu BD local
        "USER": "postgres",          # Usuario local
        "PASSWORD": "30102897",      # Tu contraseña local
        "HOST": "127.0.0.1",         # SIEMPRE localhost en desarrollo
        "PORT": "5432",
    }
}

# ========================================
# PASSWORD VALIDATION
# ========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================================
# INTERNATIONALIZATION
# ========================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ========================================
# STATIC & MEDIA (LOCAL)
# ========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"   # No se usa en local, pero no molesta

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ========================================
# POWER BI (NO SE USA EN LOCAL)
# ========================================
POWERBI_DASHBOARD_EMBED_URL = ""

# ========================================
# AUTH & USER MODEL
# ========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'usuarios.Usuario'

# ========================================
# REST + JWT
# ========================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

LOGIN_URL = 'login_django'
LOGIN_REDIRECT_URL = 'home_ciudadano'
LOGOUT_REDIRECT_URL = 'login_django'

# ========================================
# CORS (permite desarrollo sin errores)
# ========================================
CORS_ALLOW_ALL_ORIGINS = True
