

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9jvo6*u+uj&ejeg-b@o%m)jv6-xp%ufitw=h=bndb01^vq780l'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

