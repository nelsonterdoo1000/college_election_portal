import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Set default ALLOWED_HOSTS for local dev
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,213.199.34.226,cloudinary.com,api.nocenelections.com,nocenelections.com').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,213.199.34.226,cloudinary.com,api.nocenelections.com,nocenelections.com',).split(',')

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for cloudinary

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # Required for JWT blacklist functionality
    'channels',
    'corsheaders',
    'drf_spectacular',
    'cloudinary',  # Must come before cloudinary_storage
    'cloudinary_storage',  # Cloudinary for media files
    'import_export',
    'django_q',

    # Local apps
    'elections',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'election_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'elections', 'templates')],
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

WSGI_APPLICATION = 'election_portal.wsgi.application'
ASGI_APPLICATION = 'election_portal.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Channel layers for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'elections.User'

# Site ID (required for django.contrib.sites)
SITE_ID = 1

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/election_portal/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Get Cloudinary credentials from environment
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

# Cloudinary Configuration (single configuration)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Keep for compatibility

# Use Cloudinary for media files
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Optional: Use Cloudinary for static files too (uncomment if needed)
# STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Change this in production
CORS_ALLOW_CREDENTIALS = True

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'College Election Portal API',
    'DESCRIPTION': 'A comprehensive API for managing college elections with real-time voting and results.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'CONTACT': {
        'name': 'College Election Portal Team',
        'email': 'admin@nocenelections.com',
    },
    'LICENSE': {
        'name': 'MIT License',
    },
    'TAGS': [
        {'name': 'authentication', 'description': 'Authentication endpoints'},
        {'name': 'elections', 'description': 'Election management endpoints'},
        {'name': 'positions', 'description': 'Position management endpoints'},
        {'name': 'candidates', 'description': 'Candidate management endpoints'},
        {'name': 'voting', 'description': 'Voting endpoints'},
        {'name': 'users', 'description': 'User management endpoints'},
        {'name': 'audit', 'description': 'Audit log endpoints'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': True,
    },
}
CSRF_TRUSTED_ORIGINS = [
       "https://api.nocenelections.com",
       "https://nocenelections.com",
   ]
# Trust the X-Forwarded-Proto header from Nginx or Cloudflare
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Optional: Force HTTPS if needed (Disabled for local dev unless explicitly set)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'

FRONTEND_RESET_URL = os.getenv('FRONTEND_RESET_URL', 'https://nocenelections.com/reset-password')

# ZeptoMail (SMTP) settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('ZEPTO_EMAIL_HOST', 'smtp.zeptomail.com')
EMAIL_PORT = int(os.getenv('ZEPTO_EMAIL_PORT', 587))

if EMAIL_PORT == 465:
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
else:
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv('ZEPTO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('ZEPTO_EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@xpressbyte.ng')

JAZZMIN_SETTINGS = {
    "site_title": "College Election Admin",
    "site_header": "College Election",
    "site_brand": "Election Portal",
    "site_logo": "img/logo.png",
    "welcome_sign": "Welcome to the College Election Portal",
    "search_model": ["elections.User", "elections.Election"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "elections.User": "fas fa-user-graduate",
        "elections.Election": "fas fa-vote-yea",
        "elections.Position": "fas fa-briefcase",
        "elections.Candidate": "fas fa-user-tie",
        "elections.EligibleVoter": "fas fa-id-card",
        "elections.Vote": "fas fa-box",
        "elections.AuditLog": "fas fa-clipboard-list",
        "elections.OTPVerification": "fas fa-key",
    },
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "order_with_respect_to": ["elections.Election", "elections.Position", "elections.Candidate", "elections.User", "elections.EligibleVoter", "elections.Vote", "elections.AuditLog"],
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
}

# Django Q2 Configuration
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 500,
    'bulk': 10,
    'orm': 'default'
}
