from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-le-fd20vd=mh$hzoc1$i-5l-^8!2q9ny_6b#*h3!6ja=c@*t+v'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'warehouse.apps.WarehouseConfig',
    'worklog.apps.WorklogConfig',
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

ROOT_URLCONF = 'flarken.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'flarken.wsgi.application'


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'flarken',
#         'USER': 'postgres',
#         'PASSWORD': 'root',
#         'HOST': '127.0.0.1',
#         'PORT': '5433',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'flarken'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5433'),
    }
}


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


TIME_ZONE = 'UTC'

LANGUAGE_CODE = "uk"

USE_I18N = True

USE_L10N = True



STATIC_URL = 'static/'
STATIC_ROOT = '/app/staticfiles'  # куди collectstatic збирає файли

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "Склад",
    "site_header": "Склад сервісного центру",
    "site_brand": "iPhone Parts",
    "welcome_sign": "Вітаємо у системі складу",
    "copyright": "Nazar Hrynyk",

    "topmenu_links": [
        {"name": "Головна", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],

    "order_with_respect_to": [
        "warehouse",
        'warehouse.Part',
        'warehouse.PhoneModel',
        'warehouse.PartType',
        "users",
        "auth",
    ],


    "show_sidebar": True,
    "navigation_expanded": True,
    "custom_css": "styles/admin-styles.css",
    "changeform_format": "single",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-primary",
}

