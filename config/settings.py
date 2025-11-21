import os
from pathlib import Path
from datetime import timedelta

# ========================================
# BASE DIR
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================================
# SECURITY
# ========================================
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "insecure-default-key-change-in-env",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# ========================================
# HOSTS SEGUROS PARA PRODUCCIÓN
# ========================================

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'tubarriolimpio.space',
    'www.tubarriolimpio.space',
]


CSRF_TRUSTED_ORIGINS = [
    "http://100.29.99.59",
    "https://100.29.99.59",
]

# ========================================
# APPLICATIONS
# ========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'corsheaders',

    # Apps propias
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

    # CORS middleware
    'corsheaders.middleware.CorsMiddleware',

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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
# DATABASE (RDS PostgreSQL)
# ========================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "microbasurales",  
        "USER": "postgres",
        "PASSWORD": "Admin12345",
        "HOST": "instancia-microbasurales.cqvgs4di1ynp.us-east-1.rds.amazonaws.com",
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
# STATIC & MEDIA (LOCAL EN EC2)
# ========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ========================================
# POWER BI
# ========================================
POWERBI_DASHBOARD_EMBED_URL = os.environ.get(
    "POWERBI_DASHBOARD_EMBED_URL",
    ""
)

# ========================================
# AUTH
# ========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'usuarios.Usuario'

# ========================================
# REST FRAMEWORK + JWT
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

# ========================================
# CORS
# ========================================
CORS_ALLOWED_ORIGINS = [
    f"http://{host}" for host in ALLOWED_HOSTS if host
] + [
    f"https://{host}" for host in ALLOWED_HOSTS if host
]
